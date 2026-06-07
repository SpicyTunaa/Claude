"""
URL Extractor - resolves final destination URLs from a list of redirect links.

Supports two modes:
  --mode requests   Fast HTTP HEAD/GET approach for standard 301/302 redirects (default)
  --mode playwright Browser-based approach for JS-heavy pages that redirect via script
  --mode camoufox  Firefox-based stealth browser, best for anti-bot protected pages

Input:  text file with one URL per line
Output: CSV with original_url, final_url, status columns

Usage:
  python url_extractor.py links.txt
  python url_extractor.py links.txt --mode playwright --output results.csv
  python url_extractor.py links.txt --workers 20 --timeout 30
  python url_extractor.py links.txt --mode playwright --target-domain mega.nz --timeout 60
"""

import argparse
import csv
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


# ---------------------------------------------------------------------------
# Requests mode
# ---------------------------------------------------------------------------

# Patterns that embed the next hop URL inside a JS blob on the page
_EMBEDDED_LINK_PATTERNS = [
    re.compile(r"""link:\s*['"]( https?://[^'"]+)['"]"""),
    re.compile(r"""link:\s*['"]( https?://[^'"]+)['"]"""),
    re.compile(r"""['"]link['"]\s*:\s*['"]( https?://[^'"]+)['"]"""),
    re.compile(r"""conf_rew\s*=\s*\{[^}]*link:\s*['"]( https?://[^'"]+)['"]""", re.S),
    # generic: any mega / target URL in the HTML
]

# Tighter version without the accidental leading space
_EMBEDDED_LINK_PATTERNS = [
    re.compile(r"""link:\s*['"]( ?https?://[^'"]+)['"]"""),
    re.compile(r"""['"]link['"]\s*:\s*['"]( ?https?://[^'"]+)['"]"""),
]


def _extract_embedded_link(html: str) -> str | None:
    for pat in _EMBEDDED_LINK_PATTERNS:
        m = pat.search(html)
        if m:
            return m.group(1).strip()
    return None


def _follow_chain(start_url: str, timeout: int, session, target_domain: str, max_hops: int = 10) -> dict:
    """Follow a chain of HTTP redirects + embedded JS links until target_domain is found."""
    url = start_url
    visited = set()
    for _ in range(max_hops):
        if url in visited:
            break
        visited.add(url)

        if target_domain and target_domain in url:
            return {"original": start_url, "final": url, "status": 200, "error": ""}

        try:
            resp = session.get(url, timeout=timeout, allow_redirects=True)
        except Exception as exc:
            return {"original": start_url, "final": url or "", "status": "", "error": str(exc)}

        # After HTTP redirects, check if we landed on the target
        if target_domain and target_domain in resp.url:
            return {"original": start_url, "final": resp.url, "status": resp.status_code, "error": ""}

        content_type = resp.headers.get("Content-Type", "")
        if "html" not in content_type:
            # Not an HTML page — nowhere further to go
            return {"original": start_url, "final": resp.url, "status": resp.status_code, "error": ""}

        # Search for target domain anywhere in the HTML
        if target_domain:
            pat = re.compile(rf'https?://[^\s"\'<>]*{re.escape(target_domain)}[^\s"\'<>]*')
            m = pat.search(resp.text)
            if m:
                return {"original": start_url, "final": m.group(0), "status": resp.status_code, "error": ""}

        # Try to find the next embedded hop
        next_url = _extract_embedded_link(resp.text)
        if next_url and next_url != url:
            url = next_url
            continue

        # No further hop found — return current landing page
        return {"original": start_url, "final": resp.url, "status": resp.status_code, "error": ""}

    return {"original": start_url, "final": url, "status": "", "error": "max hops reached"}


def resolve_with_requests(url: str, timeout: int, session, target_domain: str) -> dict:
    try:
        return _follow_chain(url, timeout, session, target_domain)
    except Exception as exc:
        return {"original": url, "final": "", "status": "", "error": str(exc)}


def run_requests_mode(urls: list[str], workers: int, timeout: int, target_domain: str) -> list[dict]:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=workers, pool_maxsize=workers)

    results = []
    with requests.Session() as session:
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(resolve_with_requests, u, timeout, session, target_domain): u for u in urls}
            done = 0
            for future in as_completed(futures):
                results.append(future.result())
                done += 1
                print(f"\r  {done}/{len(urls)} processed", end="", flush=True)

    print()
    return results


# ---------------------------------------------------------------------------
# Playwright mode (JS-rendered redirects + countdown pages)
# ---------------------------------------------------------------------------

def _find_target_in_page(page, target_domain: str) -> str | None:
    """Search page HTML and all anchors for a URL matching target_domain."""
    html = page.content()
    pattern = rf'https?://[^\s"\'<>]*{re.escape(target_domain)}[^\s"\'<>]*'
    matches = re.findall(pattern, html)
    if matches:
        return matches[0]
    return None


def resolve_with_playwright(url: str, timeout_ms: int, target_domain: str) -> dict:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

        try:
            from playwright_stealth import stealth_sync
            _stealth = stealth_sync
        except ImportError:
            _stealth = None

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/124.0.0.0 Safari/537.36",
                locale="en-US",
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            if _stealth:
                _stealth(page)

            found_target: list[str] = []

            # Intercept navigations — catch the moment the browser lands on target_domain
            def on_response(response):
                if target_domain and target_domain in response.url:
                    found_target.append(response.url)

            if target_domain:
                page.on("response", on_response)

            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            # If target already captured via redirect interception, we're done
            if found_target:
                browser.close()
                return {"original": url, "final": found_target[0], "status": 200, "error": ""}

            # Check page HTML immediately
            hit = _find_target_in_page(page, target_domain) if target_domain else None
            if hit:
                browser.close()
                return {"original": url, "final": hit, "status": 200, "error": ""}

            # Wait up to timeout for networkidle (countdown pages finish loading)
            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except PWTimeout:
                pass

            if found_target:
                browser.close()
                return {"original": url, "final": found_target[0], "status": 200, "error": ""}

            # Scan HTML after page settles
            hit = _find_target_in_page(page, target_domain) if target_domain else None
            final = hit or page.url
            browser.close()

        return {"original": url, "final": final, "status": 200, "error": ""}

    except Exception as exc:
        return {"original": url, "final": "", "status": "", "error": str(exc)}


# ---------------------------------------------------------------------------
# Camoufox mode (Firefox with real fingerprint, best anti-bot resistance)
# ---------------------------------------------------------------------------

def resolve_with_camoufox(url: str, timeout_ms: int, target_domain: str) -> dict:
    try:
        from camoufox.sync_api import Camoufox

        with Camoufox(headless=True, geoip=True) as browser:
            page = browser.new_page()

            found_target: list[str] = []

            def on_response(response):
                if target_domain and target_domain in response.url:
                    found_target.append(response.url)

            if target_domain:
                page.on("response", on_response)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass

            if found_target:
                return {"original": url, "final": found_target[0], "status": 200, "error": ""}

            hit = _find_target_in_page(page, target_domain) if target_domain else None
            if hit:
                return {"original": url, "final": hit, "status": 200, "error": ""}

            try:
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except Exception:
                pass

            if found_target:
                return {"original": url, "final": found_target[0], "status": 200, "error": ""}

            hit = _find_target_in_page(page, target_domain) if target_domain else None
            final = hit or page.url

        return {"original": url, "final": final, "status": 200, "error": ""}
    except Exception as exc:
        return {"original": url, "final": "", "status": "", "error": str(exc)}


def run_camoufox_mode(urls: list[str], workers: int, timeout: int, target_domain: str) -> list[dict]:
    timeout_ms = timeout * 1000
    results = []
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(resolve_with_camoufox, u, timeout_ms, target_domain): u for u in urls}
        done = 0
        for future in as_completed(futures):
            results.append(future.result())
            done += 1
            print(f"\r  {done}/{len(urls)} processed", end="", flush=True)

    print()
    return results


# ---------------------------------------------------------------------------
# Extension mode (Playwright + bypass.tools extension loaded)
# ---------------------------------------------------------------------------

def _resolve_with_extension_page(page, url: str, timeout_ms: int, target_domain: str) -> dict:
    from playwright.sync_api import TimeoutError as PWTimeout

    found_target: list[str] = []

    def on_response(response):
        if target_domain and target_domain in response.url:
            found_target.append(response.url)

    if target_domain:
        page.on("response", on_response)

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    except Exception:
        pass

    deadline = time.monotonic() + timeout_ms / 1000
    final_url = None

    while time.monotonic() < deadline:
        if found_target:
            final_url = found_target[0]
            break

        try:
            # Extension sets window.dest when bypass completes
            dest = page.evaluate("() => (typeof window.dest === 'string' && window.dest) || null")
            if dest:
                final_url = dest
                break
        except Exception:
            pass

        if target_domain:
            try:
                hit = _find_target_in_page(page, target_domain)
                if hit:
                    final_url = hit
                    break
            except Exception:
                pass

            if target_domain in page.url:
                final_url = page.url
                break

        time.sleep(0.5)

    if not final_url:
        try:
            dest = page.evaluate("() => (typeof window.dest === 'string' && window.dest) || null")
            final_url = dest or page.url
        except Exception:
            final_url = page.url

    return {"original": url, "final": final_url or "", "status": 200, "error": ""}


def run_extension_mode(urls: list[str], timeout: int, target_domain: str, extension_path: str) -> list[dict]:
    import shutil
    import tempfile
    from playwright.sync_api import sync_playwright

    timeout_ms = timeout * 1000
    results = []
    user_data_dir = tempfile.mkdtemp()

    try:
        with sync_playwright() as pw:
            context = pw.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,
                args=[
                    f"--disable-extensions-except={extension_path}",
                    f"--load-extension={extension_path}",
                    "--no-sandbox",
                ],
                viewport={"width": 1280, "height": 800},
            )

            for i, url in enumerate(urls):
                page = context.new_page()
                try:
                    result = _resolve_with_extension_page(page, url, timeout_ms, target_domain)
                except Exception as exc:
                    result = {"original": url, "final": "", "status": "", "error": str(exc)}
                results.append(result)
                try:
                    page.close()
                except Exception:
                    pass
                print(f"\r  {i + 1}/{len(urls)} processed", end="", flush=True)

            context.close()
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)

    print()
    return results


def run_playwright_mode(urls: list[str], workers: int, timeout: int, target_domain: str) -> list[dict]:
    timeout_ms = timeout * 1000
    results = []
    # Playwright's sync API is not thread-safe; use processes instead
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(resolve_with_playwright, u, timeout_ms, target_domain): u for u in urls}
        done = 0
        for future in as_completed(futures):
            results.append(future.result())
            done += 1
            print(f"\r  {done}/{len(urls)} processed", end="", flush=True)

    print()
    return results


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_urls(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    urls = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    return urls


def save_results(results: list[dict], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["original", "final", "status", "error"])
        writer.writeheader()
        writer.writerows(results)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Resolve final destination URLs from a list of redirect links."
    )
    parser.add_argument("input", help="Text file with one URL per line")
    parser.add_argument(
        "--mode",
        choices=["requests", "playwright", "camoufox", "extension"],
        default="requests",
        help="Resolution method (default: requests)",
    )
    parser.add_argument(
        "--output",
        default="results.csv",
        help="Output CSV file path (default: results.csv)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Parallel workers (default: 10)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Per-URL timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--target-domain",
        default="",
        help="Domain to look for in page content, e.g. mega.nz",
    )
    parser.add_argument(
        "--extension-path",
        default="",
        help="Path to unpacked bypass extension folder (extension mode only)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    urls = load_urls(args.input)
    if not urls:
        print("No URLs found in input file.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(urls)} URLs  |  mode={args.mode}  |  workers={args.workers}")
    start = time.monotonic()

    if args.mode == "requests":
        results = run_requests_mode(urls, args.workers, args.timeout, args.target_domain)
    elif args.mode == "camoufox":
        results = run_camoufox_mode(urls, args.workers, args.timeout, args.target_domain)
    elif args.mode == "extension":
        if not args.extension_path:
            print("--extension-path is required for extension mode", file=sys.stderr)
            sys.exit(1)
        results = run_extension_mode(urls, args.timeout, args.target_domain, args.extension_path)
    else:
        results = run_playwright_mode(urls, args.workers, args.timeout, args.target_domain)

    elapsed = time.monotonic() - start
    save_results(results, args.output)

    errors = sum(1 for r in results if r["error"])
    print(f"Done in {elapsed:.1f}s  |  {len(results) - errors} OK  |  {errors} errors")
    print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()
