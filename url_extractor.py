"""
URL Extractor - resolves final destination URLs from a list of redirect links.

Supports two modes:
  --mode requests   Fast HTTP HEAD/GET approach for standard 301/302 redirects (default)
  --mode playwright Browser-based approach for JS-heavy pages that redirect via script

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

def resolve_with_requests(url: str, timeout: int, session) -> dict:
    try:
        resp = session.head(url, timeout=timeout, allow_redirects=True)
        final = resp.url

        # Some servers block HEAD; fall back to GET if we land on the same URL
        # without a redirect (could be a soft block returning 405 or 200 with no body)
        if resp.status_code == 405:
            resp = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
            resp.close()
            final = resp.url

        return {"original": url, "final": final, "status": resp.status_code, "error": ""}
    except Exception as exc:
        return {"original": url, "final": "", "status": "", "error": str(exc)}


def run_requests_mode(urls: list[str], workers: int, timeout: int) -> list[dict]:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=workers, pool_maxsize=workers)

    results = []
    with requests.Session() as session:
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; URLExtractor/1.0)"})

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(resolve_with_requests, u, timeout, session): u for u in urls}
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

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()

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
        choices=["requests", "playwright"],
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
        help="Domain to look for in page content, e.g. mega.nz (playwright mode only)",
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
        results = run_requests_mode(urls, args.workers, args.timeout)
    else:
        results = run_playwright_mode(urls, args.workers, args.timeout, args.target_domain)

    elapsed = time.monotonic() - start
    save_results(results, args.output)

    errors = sum(1 for r in results if r["error"])
    print(f"Done in {elapsed:.1f}s  |  {len(results) - errors} OK  |  {errors} errors")
    print(f"Results saved to: {args.output}")


if __name__ == "__main__":
    main()
