import { gsap } from "gsap";

/**
 * Central GSAP entry point. The Cinema Reel section only needs the core
 * timeline + easing engine (power2.out / power3.out / power4.out), so there
 * are no plugins to register here yet. `registerGSAPPlugins()` is kept as the
 * single seam for any future plugin wiring (ScrollTrigger, etc.) and is safe
 * to call repeatedly.
 */
let registered = false;

export function registerGSAPPlugins(): void {
  if (registered) return;
  registered = true;
  // No plugins required for Cinema Reel. Intentionally a no-op for now.
}

export { gsap };
