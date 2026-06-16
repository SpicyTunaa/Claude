# Cinema Reel — Vertical Film-Festival Slider

A full-viewport dark cinema scroller. Six fictional film-festival entries each
render as an 80dvh × full-width framed reel with a wide cinematic still. The deck
loads with a ~3-second motion-blurred fast-forward through every slide, scanlines
and all, before settling on slide 1 and revealing its content with a staggered
blur-in. Once seated, the user can wheel, drag, click pips, or arrow-key between
slides — everything spring-snaps to centre.

## Key behaviours

- **Entrance auto-scroll** — a single `power3.out` tween (3s) whips the deck
  through three loop-copies, driven in parallel with a 1s opacity fade-in. A
  vertical-only SVG Gaussian blur (up to 18px) and a screen-blend scanline
  overlay are velocity-driven from the tween and fade to zero as it brakes onto
  slide 1.
- **Snap physics** — a single track `translateY` springs toward
  `targetY = topPad − idx · pitch` with `y += (target − y) · 0.11`. Wheel moves
  1:1 (200px/event clamp) and live-commits the index at half-pitch. Pointer drag
  commits ±1 past 14% viewport-h, else springs back. Spring suspends for 100ms
  after the last wheel event.
- **Asymmetric content motion** — the active slide fades its content in via
  smoothstep once `|dy|/slideH ≤ 0.55`; the leaving slide keeps full opacity and
  parallax-leads (`cy = −dy × 0.42`); distant slides idle hidden.
- **Image parallax** — each image wrapper is sized `100vw × (100dvh × 1.2)` and
  translated `−dy / 1.2`, so the image lazes at 16.7% of slide speed.
- **Custom cursor** — a 104px circle carrying `SCROLL`, a grab-hand + chevrons
  on press, or a single chevron in the top/bottom 10dvh zones.
- **Detail modal** — clicking EXPLORE tilts the slide `rotateY(15deg)` on its
  left edge while a ≤640px aside slides in from the right with synopsis, stats,
  and awards. ESC, backdrop, X, or a zone-tap dismisses it.

## Implementation notes

- Every viewport-relative size uses `dvh` (never `vh`) so JS pixel math
  (`window.innerHeight`) and CSS layout stay in sync on mobile Safari.
- All time-critical state lives in refs; a single rAF loop owns the spring and
  per-slide writes. Only `autoScrolling`, `activeIdx`, and `openSlideKey` are
  React state.
- Six slides are rendered seven times (42 frames) for infinite looping; the
  index silently wraps back into the central copy near either edge.

See `src/components/sections/cinema-reel/CinemaReel.tsx` for the full
implementation. Tech: Next.js App Router, TypeScript, Tailwind CSS 4, GSAP
(timeline + easing only), raw `requestAnimationFrame`, Playfair Display.
