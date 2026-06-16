"use client";

import { useEffect, useRef, useState } from "react";
import { Playfair_Display } from "next/font/google";
import { gsap, registerGSAPPlugins } from "@/lib/animations/gsap-setup";

/* Local Playfair so the font CSS is bundled with this chunk. */
const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

/* ─── Types ───────────────────────────────────────────────────────── */
interface Award {
  stars: number;
  label: string;
  quote: string;
}
interface Stats {
  critics: number;
  audience: number;
  runtime: string;
  format: string;
  country: string;
  language: string;
  aspect: string;
}
interface Slide {
  id: string;
  badge: string;
  eyebrow: string;
  category: string;
  titleLines: string[];
  year: string;
  director: string;
  imageId: string;
  awards: Award[];
  description: string;
  stats: Stats;
}

/* ─── Section data ────────────────────────────────────────────────── */
const SLIDES: Slide[] = [
  {
    id: "blueprint-no-seven",
    badge: "true.false",
    eyebrow: "TRUE/FALSE · TRUE LIFE FUND 2024",
    category: "HYBRID DOCUMENTARY",
    titleLines: ["BLUEPRINT", "NO. 7"],
    year: "2024",
    director: "SAM BINNS",
    imageId: "1610847455028-9e55e62bac33",
    awards: [
      { stars: 5, label: "TRUE LIFE FUND", quote: "A PORTRAIT OF NOW" },
      { stars: 4, label: "BEST FIRST FEATURE", quote: "RAW & UNNERVING" },
      { stars: 5, label: "CRITICS PRIZE", quote: "ESSENTIAL VIEWING" },
    ],
    description:
      "An architect of the everyday traces seven anonymous lives across a single city block. Captured in long, unblinking takes, the film constructs an atlas of urban intimacy — strangers passing as a single organism, separated only by the gravity of their private orbits.",
    stats: {
      critics: 94,
      audience: 81,
      runtime: "1h 38m",
      format: "16MM",
      country: "UK · GERMANY",
      language: "ENGLISH",
      aspect: "1.66:1",
    },
  },
  {
    id: "atlas-unfolds",
    badge: "berlinale",
    eyebrow: "BERLINALE · ENCOUNTERS 2023",
    category: "ESSAY FILM",
    titleLines: ["ATLAS", "UNFOLDS"],
    year: "2023",
    director: "ELIAS NORÉN",
    imageId: "1596956708072-8ca0c2973887",
    awards: [
      { stars: 5, label: "BEST CINEMATOGRAPHY", quote: "AN OPULENT CANVAS" },
      { stars: 4, label: "ENCOUNTERS PRIZE", quote: "STUNNING IN RESTRAINT" },
      { stars: 5, label: "FIPRESCI PRIZE", quote: "A QUIET MASTERWORK" },
    ],
    description:
      "A four-year journey across the high passes of Central Asia, charted entirely on foot. Norén trades narration for breath and footstep — the sky is the protagonist, the path is the verse, and what unfolds is less a documentary than an epic poem to scale.",
    stats: {
      critics: 96,
      audience: 87,
      runtime: "2h 12m",
      format: "65MM",
      country: "SWEDEN · KAZAKHSTAN",
      language: "SILENT",
      aspect: "2.20:1",
    },
  },
  {
    id: "the-long-quiet",
    badge: "tiff.docs",
    eyebrow: "TIFF DOCS · PLATFORM 2024",
    category: "OBSERVATIONAL",
    titleLines: ["THE LONG", "QUIET"],
    year: "2024",
    director: "AMARA OKAFOR",
    imageId: "1633885274919-04b5af171f8c",
    awards: [
      { stars: 5, label: "PLATFORM PRIZE", quote: "DEEPLY MOVING" },
      { stars: 5, label: "BEST DIRECTOR", quote: "QUIETLY DEVASTATING" },
      { stars: 4, label: "AUDIENCE AWARD", quote: "A PORTRAIT OF SILENCE" },
    ],
    description:
      "On the eve of a six-month return to silence, four Carmelite nuns open their shutters and their letters. Okafor's patient gaze finds devotion in the smallest gestures — the way light moves across a refectory, the way silence holds a room together long after the bell has rung.",
    stats: {
      critics: 93,
      audience: 89,
      runtime: "1h 47m",
      format: "DIGITAL 4K",
      country: "NIGERIA · SPAIN",
      language: "ENGLISH · SPANISH",
      aspect: "1.85:1",
    },
  },
  {
    id: "ember-and-ash",
    badge: "venezia",
    eyebrow: "VENICE · ORIZZONTI 2025",
    category: "CHARACTER STUDY",
    titleLines: ["EMBER &", "ASH"],
    year: "2025",
    director: "MILO HAVERSTEIN",
    imageId: "1636766812350-c2842e8c6b76",
    awards: [
      { stars: 5, label: "BEST ACTRESS", quote: "SHE BURNS THE FRAME" },
      { stars: 5, label: "ORIZZONTI PRIZE", quote: "HAUNTING & PRECISE" },
      { stars: 4, label: "BEST EDITING", quote: "BURNS LONG AFTER" },
    ],
    description:
      "A wildfire memoirist returns to the village she once burned down — to face the woman she was. Haverstein's chamber drama burns at one steady temperature, then explodes. A career-defining lead carries the entire frame on the slow inhale of a final cigarette.",
    stats: {
      critics: 92,
      audience: 84,
      runtime: "1h 56m",
      format: "35MM",
      country: "GERMANY · ITALY",
      language: "GERMAN · ITALIAN",
      aspect: "2.39:1",
    },
  },
  {
    id: "cavern",
    badge: "rotterdam",
    eyebrow: "TIGER COMPETITION · IFFR 2022",
    category: "EXPERIMENTAL",
    titleLines: ["CAVERN"],
    year: "2022",
    director: "SØREN HOLT",
    imageId: "1665426520283-33b35e81bbc7",
    awards: [
      { stars: 5, label: "TIGER AWARD", quote: "ARCHITECTURE OF FEELING" },
      { stars: 4, label: "VPRO BIG SCREEN", quote: "OBSESSIVELY COMPOSED" },
      { stars: 5, label: "FIPRESCI PRIZE", quote: "A NEW LANGUAGE" },
    ],
    description:
      "Eight composers, eight subterranean chambers, one resonant frequency. Holt's experimental documentary descends literally into the earth to record what stone remembers when struck. The result: a film you don't watch so much as feel from the diaphragm out.",
    stats: {
      critics: 89,
      audience: 76,
      runtime: "1h 24m",
      format: "DIGITAL 4K",
      country: "DENMARK · NORWAY",
      language: "DANISH",
      aspect: "1.43:1",
    },
  },
  {
    id: "where-light-breaks",
    badge: "cannes",
    eyebrow: "DIRECTORS' FORTNIGHT · CANNES 2024",
    category: "LYRICAL DOCUMENTARY",
    titleLines: ["WHERE LIGHT", "BREAKS"],
    year: "2024",
    director: "INGRID HALLE",
    imageId: "1615374744335-dd8adbd9e3e9",
    awards: [
      { stars: 5, label: "ART CINEMA AWARD", quote: "A PRAYER OF A FILM" },
      { stars: 5, label: "BEST CINEMATOGRAPHY", quote: "LIGHT AS CHARACTER" },
      { stars: 4, label: "PRIX CINÉMA", quote: "TENDER AND TRUE" },
    ],
    description:
      "Three generations of foresters, one mountain ridge, an unbroken century. Halle returns to her grandmother's valley with a camera that is older than she is and a question that is older than the trees. What we keep, what we lose, what the light decides.",
    stats: {
      critics: 95,
      audience: 91,
      runtime: "1h 41m",
      format: "16MM",
      country: "NORWAY · FINLAND",
      language: "NORWEGIAN",
      aspect: "1.66:1",
    },
  },
];

/* ─── Layout (vh values; rendered as dvh) ─────────────────────────── */
const SLIDE_VH = 80;
const GAP_VH = 5;
const PITCH_VH = SLIDE_VH + GAP_VH; // 85
const PAD_X_VH = 7.5;
const MASK_VH = 10;
const TOP_PAD_VH = (100 - SLIDE_VH) / 2; // 10

/* ─── Input thresholds ────────────────────────────────────────────── */
const WHEEL_PER_EVENT_CAP = 200;
const WHEEL_PAUSE_MS = 100;
const DRAG_THRESHOLD_VH = 14;

/* ─── Spring ──────────────────────────────────────────────────────── */
const EASE = 0.11;

/* ─── Content motion ──────────────────────────────────────────────── */
const FADE_THRESHOLD = 0.55;
const PARALLAX_FACTOR = 0.42;
const ENTRY_OFFSET_PX = 64;

/* ─── Image parallax ──────────────────────────────────────────────── */
const IMG_HEIGHT_RATIO = 1.2;

/* ─── Loop ────────────────────────────────────────────────────────── */
const LOOP_COPIES = 7;
const N_SLIDES = SLIDES.length; // 6
const TOTAL_RENDERED = N_SLIDES * LOOP_COPIES; // 42
const INITIAL_IDX = Math.floor(LOOP_COPIES / 2) * N_SLIDES; // 18

/* ─── Auto-scroll entrance ────────────────────────────────────────── */
const AUTO_START_IDX = INITIAL_IDX + 1; // 19
const AUTO_END_IDX = INITIAL_IDX + 3 * N_SLIDES; // 36
const AUTO_SCROLL_MS = 3000;
const AUTO_SCALE_FROM = 1;
const AUTO_FADE_MS = 1000;

/* ─── Cursor ──────────────────────────────────────────────────────── */
const CURSOR_SIZE = 104;

/* ─── Background ──────────────────────────────────────────────────── */
const BG = "#0a0908";

/* ─── Image source policy ─────────────────────────────────────────── */
const IMG_BUCKET_PX = 50;
const IMG_MIN_W = 600;
const IMG_MIN_H = 500;

function computeImgDims(): { w: number; h: number } {
  if (typeof window === "undefined") return { w: 2400, h: 1800 };
  const w = Math.max(
    IMG_MIN_W,
    Math.round(window.innerWidth / IMG_BUCKET_PX) * IMG_BUCKET_PX,
  );
  const h = Math.max(
    IMG_MIN_H,
    Math.round((window.innerHeight * IMG_HEIGHT_RATIO) / IMG_BUCKET_PX) *
      IMG_BUCKET_PX,
  );
  return { w, h };
}

function imgUrl(imageId: string, w: number, h: number, q = 75): string {
  return `https://images.unsplash.com/photo-${imageId}?w=${w}&h=${h}&fit=crop&q=${q}&auto=format`;
}

const modN = (i: number) => ((i % N_SLIDES) + N_SLIDES) % N_SLIDES;

/* ═══════════════════════════════════════════════════════════════════
   CinemaReel — default export
   ═══════════════════════════════════════════════════════════════════ */
export default function CinemaReel({ className }: { className?: string }) {
  const [autoScrolling, setAutoScrolling] = useState(true);
  const [activeIdx, setActiveIdx] = useState(modN(AUTO_START_IDX)); // → "02"
  const [openSlideKey, setOpenSlideKey] = useState<string | null>(null);
  const [openSlotIdx, setOpenSlotIdx] = useState<number | null>(null);
  const [imgDims, setImgDims] = useState<{ w: number; h: number }>(() =>
    computeImgDims(),
  );

  /* Single close path so every dismiss mechanism clears both keys. */
  const closeModal = () => {
    setOpenSlideKey(null);
    setOpenSlotIdx(null);
  };

  /* Refs — all time-critical state lives here so the rAF loop never re-renders. */
  const sectionRef = useRef<HTMLElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const slideRefs = useRef<(HTMLDivElement | null)[]>([]);
  const cursorRef = useRef<HTMLDivElement>(null);
  const cursorScrollRef = useRef<HTMLDivElement>(null);
  const cursorDragRef = useRef<HTMLDivElement>(null);
  const cursorUpRef = useRef<HTMLDivElement>(null);
  const cursorDownRef = useRef<HTMLDivElement>(null);
  const cursorOnUiRef = useRef(false);
  const cursorZoneRef = useRef<"top" | "bottom" | null>(null);

  const idxRef = useRef(AUTO_START_IDX);
  const prevIdxRef = useRef(AUTO_START_IDX);
  const yRef = useRef(0);
  const velRef = useRef(0);
  const targetYRef = useRef(0);
  const wheelLastTime = useRef(0);
  const autoScrollingRef = useRef(true);

  const blurFilterRef = useRef<SVGFEGaussianBlurElement | null>(null);
  const scanlinesRef = useRef<HTMLDivElement | null>(null);
  const lastBlurPRef = useRef(0);
  const lastBlurTsRef = useRef(0);

  const dragRef = useRef({
    active: false,
    startClientY: 0,
    startTrackY: 0,
    delta: 0,
    pointerId: 0 as number,
  });
  const onSectionRef = useRef(false);
  const downRef = useRef(false);

  const cursorPos = useRef({ x: 0, y: 0 });
  const cursorRender = useRef({ x: 0, y: 0, scale: 0, opacity: 0 });
  const cursorInitRef = useRef(false);

  const navigateToModRef = useRef<(target: number) => void>(() => {});
  const openSlideKeyRef = useRef<string | null>(null);

  /* Mirror modal state into a ref for the open/close key handler. */
  useEffect(() => {
    openSlideKeyRef.current = openSlideKey;
  }, [openSlideKey]);

  /* Recompute image bucket on resize + preload all slide images. */
  useEffect(() => {
    const onResize = () => setImgDims(computeImgDims());
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    SLIDES.forEach((slide) => {
      const img = new window.Image();
      img.src = imgUrl(slide.imageId, imgDims.w, imgDims.h);
    });
  }, [imgDims.w, imgDims.h]);

  /* Escape closes the open detail panel. */
  useEffect(() => {
    if (openSlideKey == null) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpenSlideKey(null);
        setOpenSlotIdx(null);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [openSlideKey]);

  /* ─── The single master effect ─────────────────────────────────── */
  useEffect(() => {
    registerGSAPPlugins();
    const section = sectionRef.current;
    const track = trackRef.current;
    if (!section || !track) return;

    /* ── Layout sizes ── */
    let viewportH = window.innerHeight;
    let pitch = (viewportH * PITCH_VH) / 100;
    let slideH = (viewportH * SLIDE_VH) / 100;
    let dragThresh = (viewportH * DRAG_THRESHOLD_VH) / 100;
    let topPad = (viewportH * TOP_PAD_VH) / 100;

    const recomputeSizes = () => {
      viewportH = window.innerHeight;
      pitch = (viewportH * PITCH_VH) / 100;
      slideH = (viewportH * SLIDE_VH) / 100;
      dragThresh = (viewportH * DRAG_THRESHOLD_VH) / 100;
      topPad = (viewportH * TOP_PAD_VH) / 100;
      if (!autoScrollingRef.current) {
        targetYRef.current = topPad - idxRef.current * pitch;
        yRef.current = targetYRef.current;
      }
    };
    recomputeSizes();

    /* Initial yRef uses the VISUAL pitch at scale AUTO_SCALE_FROM (= 1). */
    {
      const initialVPitchVh = SLIDE_VH * AUTO_SCALE_FROM + GAP_VH; // 85
      yRef.current =
        ((TOP_PAD_VH - AUTO_START_IDX * initialVPitchVh) * window.innerHeight) /
        100;
      targetYRef.current = yRef.current;
    }

    /* ── Loop wrap helpers ── */
    const maybeWrap = () => {
      while (idxRef.current < N_SLIDES) {
        idxRef.current += N_SLIDES;
        prevIdxRef.current += N_SLIDES;
        const shift = N_SLIDES * pitch;
        yRef.current -= shift;
        targetYRef.current -= shift;
        if (dragRef.current.active) dragRef.current.startTrackY -= shift;
      }
      while (idxRef.current >= (LOOP_COPIES - 1) * N_SLIDES) {
        idxRef.current -= N_SLIDES;
        prevIdxRef.current -= N_SLIDES;
        const shift = N_SLIDES * pitch;
        yRef.current += shift;
        targetYRef.current += shift;
        if (dragRef.current.active) dragRef.current.startTrackY += shift;
      }
    };

    const setIndex = (next: number) => {
      if (next === idxRef.current) return;
      prevIdxRef.current = idxRef.current;
      idxRef.current = next;
      targetYRef.current = topPad - next * pitch;
      setActiveIdx(modN(next));
      maybeWrap();
    };

    navigateToModRef.current = (targetMod: number) => {
      const currentMod = modN(idxRef.current);
      let diff = targetMod - currentMod;
      if (diff > N_SLIDES / 2) diff -= N_SLIDES;
      else if (diff < -N_SLIDES / 2) diff += N_SLIDES;
      if (diff === 0) return;
      setIndex(idxRef.current + diff);
    };

    /* ── Entrance timeline ── */
    const tweenObj = { p: 0 };
    const SCROLL_TOTAL_S = AUTO_SCROLL_MS / 1000; // 3
    const FADE_S = AUTO_FADE_MS / 1000; // 1
    const slideEls = slideRefs.current;
    const vhToPx = window.innerHeight / 100;

    const onScrollUpdate = () => {
      const p = tweenObj.p;
      const scale = AUTO_SCALE_FROM + (1 - AUTO_SCALE_FROM) * p; // === 1
      const idxF = AUTO_START_IDX + (AUTO_END_IDX - AUTO_START_IDX) * p;
      const vpVh = SLIDE_VH * scale + GAP_VH;

      yRef.current = (TOP_PAD_VH - idxF * vpVh) * vhToPx;
      targetYRef.current = yRef.current;

      const deltaVh = SLIDE_VH * (scale - 1); // 0 at scale 1
      const visualPitchPx = vpVh * vhToPx;
      for (let i = 0; i < slideEls.length; i++) {
        const el = slideEls[i];
        if (el) {
          el.style.transform = `translate3d(0, ${(i * deltaVh).toFixed(
            3,
          )}dvh, 0) scale(${scale.toFixed(4)})`;
          const cache = el as unknown as { __wrap?: HTMLElement | null };
          if (cache.__wrap === undefined) {
            cache.__wrap = el.querySelector(
              "[data-slide-image]",
            ) as HTMLElement | null;
          }
          if (cache.__wrap) {
            const visualDyPx = (i - idxF) * visualPitchPx;
            const wrapY = -visualDyPx / (IMG_HEIGHT_RATIO * scale);
            cache.__wrap.style.transform = `translate3d(0, ${wrapY.toFixed(
              2,
            )}px, 0)`;
          }
        }
      }

      /* Velocity-driven motion blur + scanlines. */
      const now = performance.now();
      let norm = 1;
      if (lastBlurTsRef.current > 0) {
        const dt = Math.max(now - lastBlurTsRef.current, 1);
        const dp = Math.abs(p - lastBlurPRef.current);
        const idxRange = AUTO_END_IDX - AUTO_START_IDX;
        const idxSpeed = (dp * idxRange) / dt;
        const peakSpeed = (idxRange * 3) / (SCROLL_TOTAL_S * 1000);
        norm = Math.min(idxSpeed / peakSpeed, 1);
      }
      lastBlurPRef.current = p;
      lastBlurTsRef.current = now;

      if (blurFilterRef.current) {
        blurFilterRef.current.setAttribute(
          "stdDeviation",
          `0 ${(norm * 18).toFixed(2)}`,
        );
      }
      if (scanlinesRef.current) {
        scanlinesRef.current.style.opacity = norm.toFixed(3);
      }
    };

    let timelineCompletedOnce = false;
    const mainTween = gsap.timeline({
      onUpdate: onScrollUpdate,
      onComplete: () => {
        if (timelineCompletedOnce) return;
        timelineCompletedOnce = true;
        for (let i = 0; i < slideEls.length; i++) {
          const el = slideEls[i];
          if (el) el.style.transform = "";
        }
        if (blurFilterRef.current) {
          blurFilterRef.current.setAttribute("stdDeviation", "0 0");
        }
        autoScrollingRef.current = false;
        setAutoScrolling(false);
        idxRef.current = AUTO_END_IDX;
        prevIdxRef.current = AUTO_END_IDX;
        targetYRef.current = topPad - AUTO_END_IDX * pitch;
        yRef.current = targetYRef.current;
        setActiveIdx(modN(AUTO_END_IDX));
        maybeWrap();

        const landing = slideRefs.current[idxRef.current];
        if (landing) {
          const reveals = landing.querySelectorAll<HTMLElement>("[data-reveal]");
          if (reveals.length) {
            gsap.fromTo(
              reveals,
              { autoAlpha: 0, y: 32, filter: "blur(10px)" },
              {
                autoAlpha: 1,
                y: 0,
                filter: "blur(0px)",
                duration: 1.0,
                ease: "power4.out",
                stagger: 0.07,
              },
            );
          }
        }
      },
    });

    mainTween.to(
      slideEls.filter(Boolean),
      { autoAlpha: 1, duration: FADE_S, ease: "power2.out" },
      0,
    );
    mainTween.to(
      tweenObj,
      { p: 1, duration: SCROLL_TOTAL_S, ease: "power3.out" },
      0,
    );

    /* ── rAF loop ── */
    let raf = 0;
    const tick = () => {
      const now = performance.now();
      const isDragging = dragRef.current.active;
      const wheelActive = now - wheelLastTime.current < WHEEL_PAUSE_MS;
      const isAutoScrolling = autoScrollingRef.current;

      if (!isDragging && !wheelActive && !isAutoScrolling) {
        const dy = targetYRef.current - yRef.current;
        if (Math.abs(dy) < 0.5) yRef.current = targetYRef.current;
        else yRef.current += dy * EASE;
      }
      velRef.current = 0;
      track.style.transform = `translate3d(0, ${yRef.current}px, 0)`;
      const y = yRef.current;

      const viewCenter = viewportH / 2;
      for (let i = 0; i < TOTAL_RENDERED; i++) {
        const ref = slideRefs.current[i];
        if (!ref) continue;

        const effectiveTop = i * pitch + y;
        const slideCenter = effectiveTop + slideH / 2;
        const dy = slideCenter - viewCenter;
        const dn = Math.abs(dy) / slideH;

        if (dn > 2) {
          const content = ref.querySelector(
            "[data-slide-content]",
          ) as HTMLElement | null;
          if (content && content.style.opacity !== "0") {
            content.style.opacity = "0";
            content.style.filter = "blur(16px)";
          }
          continue;
        }

        const cache = ref as unknown as { __wrap?: HTMLElement | null };
        let wrap = cache.__wrap;
        if (wrap === undefined) {
          wrap = ref.querySelector("[data-slide-image]") as HTMLElement | null;
          cache.__wrap = wrap;
        }
        const content = ref.querySelector(
          "[data-slide-content]",
        ) as HTMLElement | null;
        if (!content) continue;

        if (wrap && !isAutoScrolling) {
          const imgY = -dy / IMG_HEIGHT_RATIO;
          wrap.style.transform = `translate3d(0, ${imgY.toFixed(2)}px, 0)`;
        }

        if (isAutoScrolling) {
          if (content.style.opacity !== "0") {
            content.style.opacity = "0";
            content.style.filter = "blur(16px)";
          }
          continue;
        }

        const isActive = i === idxRef.current;
        const isLeaving =
          i === prevIdxRef.current && prevIdxRef.current !== idxRef.current;

        let opacity = 0;
        let blur = 16;
        let cy = 0;

        if (isActive) {
          const t = Math.max(0, Math.min(1, 1 - dn / FADE_THRESHOLD));
          opacity = t * t * (3 - 2 * t);
          blur = (1 - opacity) * 14;
          cy = (1 - opacity) * ENTRY_OFFSET_PX * Math.sign(dy || 1);
        } else if (isLeaving) {
          const fade = Math.max(0, 1 - Math.max(0, dn - 0.6) / 0.6);
          opacity = fade;
          blur = (1 - fade) * 6;
          cy = -dy * PARALLAX_FACTOR;
        } else {
          opacity = 0;
          blur = 16;
          cy = 0;
        }

        content.style.transform = `translate3d(0, ${cy.toFixed(2)}px, 0)`;
        content.style.opacity = opacity.toFixed(3);
        content.style.filter = `blur(${blur.toFixed(2)}px)`;
      }

      /* Cursor follow + state machine. */
      const cur = cursorRef.current;
      if (cur) {
        const px = cursorPos.current.x;
        const py = cursorPos.current.y;
        if (!cursorInitRef.current && (px !== 0 || py !== 0)) {
          cursorRender.current.x = px;
          cursorRender.current.y = py;
          cursorInitRef.current = true;
        }
        cursorRender.current.x += (px - cursorRender.current.x) * 0.22;
        cursorRender.current.y += (py - cursorRender.current.y) * 0.22;
        const targetOpacity =
          onSectionRef.current && cursorInitRef.current ? 1 : 0;
        cursorRender.current.opacity +=
          (targetOpacity - cursorRender.current.opacity) * 0.18;
        const targetScale = downRef.current ? 1.18 : 1;
        cursorRender.current.scale +=
          (targetScale - cursorRender.current.scale) * 0.22;

        cur.style.transform =
          `translate3d(${cursorRender.current.x}px, ${cursorRender.current.y}px, 0) ` +
          `translate(-50%, -50%) ` +
          `scale(${cursorRender.current.scale.toFixed(3)})`;
        cur.style.opacity = cursorRender.current.opacity.toFixed(3);

        const zone = cursorZoneRef.current;
        const isDown = downRef.current;
        const onUi = cursorOnUiRef.current;
        if (cursorScrollRef.current)
          cursorScrollRef.current.style.opacity =
            zone === null && !isDown && !onUi ? "1" : "0";
        if (cursorDragRef.current)
          cursorDragRef.current.style.opacity =
            isDown && zone === null ? "1" : "0";
        if (cursorUpRef.current)
          cursorUpRef.current.style.opacity =
            zone === "top" || (isDown && zone === null) ? "1" : "0";
        if (cursorDownRef.current)
          cursorDownRef.current.style.opacity =
            zone === "bottom" || (isDown && zone === null) ? "1" : "0";
      }

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    /* ── Wheel ── */
    const onWheel = (e: WheelEvent) => {
      if (!onSectionRef.current) return;
      const target = e.target as HTMLElement | null;
      if (target?.closest("[data-no-drag]")) return;

      e.preventDefault();
      const delta = Math.max(
        -WHEEL_PER_EVENT_CAP,
        Math.min(WHEEL_PER_EVENT_CAP, e.deltaY),
      );
      yRef.current -= delta;
      wheelLastTime.current = performance.now();

      const idealFloat = (topPad - yRef.current) / pitch;
      const nearest = Math.round(idealFloat);
      if (nearest !== idxRef.current) setIndex(nearest);
    };

    /* ── Pointer drag ── */
    const onPointerDown = (e: PointerEvent) => {
      if (!onSectionRef.current) return;
      if (e.pointerType === "mouse" && e.button !== 0) return;
      const target = e.target as HTMLElement | null;
      if (target?.closest("[data-no-drag]")) return;
      wheelLastTime.current = 0;
      dragRef.current.active = true;
      dragRef.current.startClientY = e.clientY;
      dragRef.current.startTrackY = yRef.current;
      dragRef.current.delta = 0;
      dragRef.current.pointerId = e.pointerId;
      downRef.current = true;
      try {
        section.setPointerCapture(e.pointerId);
      } catch {
        /* detached */
      }
    };

    const onPointerMove = (e: PointerEvent) => {
      cursorPos.current.x = e.clientX;
      cursorPos.current.y = e.clientY;
      const topThreshold = (window.innerHeight * MASK_VH) / 100;
      const bottomThreshold =
        window.innerHeight - (window.innerHeight * MASK_VH) / 100;
      if (e.clientY < topThreshold) cursorZoneRef.current = "top";
      else if (e.clientY > bottomThreshold) cursorZoneRef.current = "bottom";
      else cursorZoneRef.current = null;
      cursorOnUiRef.current = !!(
        e.target as HTMLElement | null
      )?.closest("[data-no-drag]");

      if (!dragRef.current.active) return;
      const delta = e.clientY - dragRef.current.startClientY;
      dragRef.current.delta = delta;
      yRef.current = dragRef.current.startTrackY + delta;
      velRef.current = 0;
    };

    const endDrag = (committed: boolean) => {
      const delta = dragRef.current.delta;
      const zone = cursorZoneRef.current;
      dragRef.current.active = false;
      downRef.current = false;
      if (!committed) return;

      if (zone && Math.abs(delta) < 8) {
        const next = idxRef.current + (zone === "top" ? -1 : 1);
        setOpenSlideKey(null);
        setOpenSlotIdx(null);
        setIndex(next);
        return;
      }
      if (Math.abs(delta) > dragThresh) {
        const next = idxRef.current + (delta < 0 ? 1 : -1);
        setIndex(next);
      }
    };

    const onPointerUp = () => {
      if (!dragRef.current.active) return;
      try {
        section.releasePointerCapture(dragRef.current.pointerId);
      } catch {
        /* detached */
      }
      endDrag(true);
    };
    const onPointerCancel = () => {
      dragRef.current.delta = 0;
      yRef.current = dragRef.current.startTrackY;
      endDrag(false);
    };

    /* ── Enter/leave + keyboard ── */
    const onEnter = () => {
      onSectionRef.current = true;
    };
    const onLeave = () => {
      onSectionRef.current = false;
      if (dragRef.current.active) endDrag(true);
    };
    const onResize = () => recomputeSizes();
    const onKey = (e: KeyboardEvent) => {
      if (!onSectionRef.current) return;
      if (e.key === "ArrowDown" || e.key === "PageDown" || e.key === " ") {
        e.preventDefault();
        setIndex(idxRef.current + 1);
      } else if (e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        setIndex(idxRef.current - 1);
      }
    };

    section.addEventListener("wheel", onWheel, { passive: false });
    section.addEventListener("pointerdown", onPointerDown);
    section.addEventListener("pointermove", onPointerMove);
    section.addEventListener("pointerup", onPointerUp);
    section.addEventListener("pointercancel", onPointerCancel);
    section.addEventListener("pointerenter", onEnter);
    section.addEventListener("pointerleave", onLeave);
    window.addEventListener("resize", onResize);
    window.addEventListener("keydown", onKey);

    return () => {
      cancelAnimationFrame(raf);
      mainTween.kill();
      section.removeEventListener("wheel", onWheel);
      section.removeEventListener("pointerdown", onPointerDown);
      section.removeEventListener("pointermove", onPointerMove);
      section.removeEventListener("pointerup", onPointerUp);
      section.removeEventListener("pointercancel", onPointerCancel);
      section.removeEventListener("pointerenter", onEnter);
      section.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  const handlePipClick = (mod: number) => {
    navigateToModRef.current(mod);
  };

  const openSlide =
    openSlideKey != null ? SLIDES.find((s) => s.id === openSlideKey) ?? null : null;

  return (
    <section
      ref={sectionRef}
      className={`relative h-[100dvh] w-full overflow-hidden select-none [--cinema-pad-x:7.5dvh] max-sm:[--cinema-pad-x:2dvh] ${
        className ?? ""
      }`}
      style={{ background: BG, cursor: "none" }}
    >
      {/* Off-screen SVG filter defs */}
      <svg
        aria-hidden
        focusable={false}
        className="pointer-events-none absolute"
        style={{ width: 0, height: 0, position: "absolute" }}
      >
        <defs>
          <filter
            id="cinema-motion-blur"
            x="-5%"
            y="-25%"
            width="110%"
            height="150%"
          >
            <feGaussianBlur
              ref={blurFilterRef}
              in="SourceGraphic"
              stdDeviation="0 0"
            />
          </filter>
        </defs>
      </svg>

      {/* Track */}
      <div
        ref={trackRef}
        className="absolute inset-x-0 top-0"
        style={{
          touchAction: "none",
          paddingLeft: "var(--cinema-pad-x)",
          paddingRight: "var(--cinema-pad-x)",
          transform: `translate3d(0, ${
            TOP_PAD_VH - AUTO_START_IDX * (SLIDE_VH * AUTO_SCALE_FROM + GAP_VH)
          }dvh, 0)`,
        }}
      >
        {Array.from({ length: TOTAL_RENDERED }).map((_, i) => {
          const slide = SLIDES[modN(i)];
          const isFirst = i === AUTO_END_IDX;
          return (
            <SlideFrame
              key={i}
              slide={slide}
              isFirst={isFirst}
              imgDims={imgDims}
              slotIndex={i}
              autoScrolling={autoScrolling}
              isOpen={openSlotIdx === i}
              onExplore={() => {
                setOpenSlideKey(slide.id);
                setOpenSlotIdx(i);
              }}
              assignRef={(el) => {
                slideRefs.current[i] = el;
              }}
            />
          );
        })}
      </div>

      {/* Top + bottom masks */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 z-30"
        style={{
          height: `${MASK_VH}dvh`,
          background: `linear-gradient(180deg, ${BG} 0%, rgba(10,9,8,0) 100%)`,
        }}
      />
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 z-30"
        style={{
          height: `${MASK_VH}dvh`,
          background: `linear-gradient(0deg, ${BG} 0%, rgba(10,9,8,0) 100%)`,
        }}
      />

      {/* Scanlines (auto-scroll only) */}
      {autoScrolling && (
        <div
          ref={scanlinesRef}
          aria-hidden
          className="pointer-events-none absolute inset-0 z-[25]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, " +
              "rgba(255,255,255,0.06) 0px, rgba(255,255,255,0.06) 1px, " +
              "transparent 1px, transparent 3px)",
            mixBlendMode: "screen",
            opacity: 1,
          }}
        />
      )}

      {/* Right-edge indicator */}
      <ReelIndicator
        activeIdx={activeIdx}
        total={N_SLIDES}
        font={playfair.className}
        onPipClick={handlePipClick}
        hidden={openSlideKey != null}
      />

      {/* Detail modal */}
      <DetailsPanel
        open={openSlideKey != null}
        slide={openSlide}
        imgDims={imgDims}
        onClose={closeModal}
      />

      {/* Custom cursor */}
      <div
        ref={cursorRef}
        className="pointer-events-none fixed left-0 top-0 z-50"
        style={{
          width: CURSOR_SIZE,
          height: CURSOR_SIZE,
          opacity: 0,
          willChange: "transform, opacity",
        }}
      >
        <div className="relative h-full w-full">
          <div className="absolute inset-0 rounded-full border border-white/45" />
          <div
            ref={cursorScrollRef}
            className="absolute inset-0 flex items-center justify-center"
            style={{ transition: "opacity 180ms ease" }}
          >
            <span className="text-[10px] font-medium uppercase tracking-[0.32em] text-white">
              SCROLL
            </span>
          </div>
          <div
            ref={cursorDragRef}
            className="absolute inset-0 flex items-center justify-center"
            style={{ opacity: 0, transition: "opacity 160ms ease" }}
          >
            <GrabHand />
          </div>
          <div
            ref={cursorUpRef}
            className="absolute"
            style={{
              bottom: "calc(100% + 12px)",
              left: "50%",
              transform: "translateX(-50%)",
              opacity: 0,
              transition: "opacity 160ms ease",
            }}
          >
            <ChevronGlyph />
          </div>
          <div
            ref={cursorDownRef}
            className="absolute"
            style={{
              top: "calc(100% + 12px)",
              left: "50%",
              transform: "translateX(-50%) rotate(180deg)",
              opacity: 0,
              transition: "opacity 160ms ease",
            }}
          >
            <ChevronGlyph />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   SlideFrame
   ═══════════════════════════════════════════════════════════════════ */
function SlideFrame({
  slide,
  isFirst,
  imgDims,
  slotIndex,
  autoScrolling,
  isOpen,
  onExplore,
  assignRef,
}: {
  slide: Slide;
  isFirst: boolean;
  imgDims: { w: number; h: number };
  slotIndex: number;
  autoScrolling: boolean;
  isOpen: boolean;
  onExplore: () => void;
  assignRef: (el: HTMLDivElement | null) => void;
}) {
  const initialTranslate = slotIndex * SLIDE_VH * (AUTO_SCALE_FROM - 1); // 0
  const initialStyle = autoScrolling
    ? {
        transform: `translate3d(0, ${initialTranslate}dvh, 0) scale(${AUTO_SCALE_FROM})`,
        transformOrigin: "50% 50%" as const,
        opacity: 0,
      }
    : undefined;

  return (
    <div
      ref={assignRef}
      className="relative w-full"
      style={{
        height: `${SLIDE_VH}dvh`,
        marginBottom: `${GAP_VH}dvh`,
        perspective: "2000px",
        ...initialStyle,
      }}
    >
      <div
        className="relative h-full w-full overflow-hidden"
        style={{
          borderRadius: "48px",
          transformOrigin: "0% 50%",
          transformStyle: "preserve-3d",
          transform: isOpen ? "rotateY(15deg)" : undefined,
          transition:
            "transform 700ms cubic-bezier(0.22, 1, 0.36, 1), " +
            "box-shadow 700ms cubic-bezier(0.22, 1, 0.36, 1)",
          boxShadow: isOpen
            ? "0 30px 80px -20px rgba(0,0,0,0.55), 0 8px 30px -10px rgba(0,0,0,0.35)"
            : undefined,
        }}
      >
        {/* Image wrapper */}
        <div
          data-slide-image
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: "100vw",
            height: `${IMG_HEIGHT_RATIO * 100}dvh`,
            marginTop: `${-IMG_HEIGHT_RATIO * 50}dvh`,
            marginLeft: "-50vw",
            willChange: "transform",
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imgUrl(slide.imageId, imgDims.w, imgDims.h)}
            alt=""
            loading="eager"
            decoding="async"
            fetchPriority={isFirst ? "high" : "auto"}
            draggable={false}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              display: "block",
            }}
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                "linear-gradient(180deg, " +
                "rgba(0,0,0,0.42) 0%, " +
                "rgba(0,0,0,0.06) 22%, " +
                "rgba(0,0,0,0.04) 70%, " +
                "rgba(0,0,0,0.55) 100%)",
            }}
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                "radial-gradient(80% 70% at 50% 50%, " +
                "transparent 40%, " +
                "rgba(0,0,0,0.45) 100%)",
            }}
          />
        </div>

        {/* Content layer */}
        <div
          data-slide-content
          className="absolute inset-0 will-change-[opacity,filter,transform]"
          style={{ opacity: 0, filter: "blur(16px)" }}
        >
          <SlideContent slide={slide} onExplore={onExplore} />
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   SlideContent
   ═══════════════════════════════════════════════════════════════════ */
function SlideContent({
  slide,
  onExplore,
}: {
  slide: Slide;
  onExplore: () => void;
}) {
  return (
    <div className="relative h-full w-full p-[5.5dvh_6dvh] text-white max-sm:p-[3dvh]">
      {/* A. TOP-LEFT */}
      <div
        className="absolute left-[6dvh] top-[5.5dvh] flex flex-col gap-3 max-sm:left-[3dvh] max-sm:top-[3dvh] max-sm:gap-2"
        data-reveal
      >
        <div
          className={`${playfair.className} text-[clamp(1.2rem,2.2dvh,2.4rem)] leading-none text-white/90`}
          style={{ fontStyle: "italic" }}
        >
          {slide.year}
        </div>

        <div className="text-[10px] font-medium uppercase tracking-[0.32em] text-white/65 max-sm:text-[8.5px] max-sm:tracking-[0.24em]">
          {slide.eyebrow.split(" ").map((word, i, arr) => (
            <span key={i}>
              {word}
              {i === Math.floor(arr.length / 2) - 1 ? (
                <br />
              ) : i < arr.length - 1 ? (
                " "
              ) : (
                ""
              )}
            </span>
          ))}
        </div>

        <div className="mt-3 inline-flex items-center gap-0 max-sm:hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/left-award-symbol.svg"
            alt=""
            aria-hidden
            className="h-[44px] w-[28px] shrink-0"
            style={{
              marginRight: -10,
              filter: "brightness(0) invert(1)",
              opacity: 0.85,
            }}
          />
          <div className="flex flex-col items-center gap-1">
            <span
              className={`${playfair.className} text-[10px] font-bold tracking-wide text-white/85`}
            >
              Award-Winning Reel
            </span>
            <div className="flex gap-[2px]">
              {Array.from({ length: 5 }).map((_, i) => (
                <svg key={i} width="9" height="9" viewBox="0 0 24 24" aria-hidden>
                  <polygon
                    points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"
                    className="fill-white/65"
                  />
                </svg>
              ))}
            </div>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/right-award-symbol.svg"
            alt=""
            aria-hidden
            className="h-[44px] w-[28px] shrink-0"
            style={{
              marginLeft: -10,
              filter: "brightness(0) invert(1)",
              opacity: 0.85,
            }}
          />
        </div>
      </div>

      {/* B. CENTER-LEFT */}
      <div
        className="absolute left-[6dvh] flex flex-col gap-5 max-sm:left-[3dvh] max-sm:gap-3"
        style={{ bottom: "9dvh" }}
        data-reveal
      >
        <div className="text-[10px] font-medium uppercase tracking-[0.4em] text-white/55 max-sm:text-[8.5px] max-sm:tracking-[0.28em]">
          {slide.category}
        </div>

        <h2
          className={`${playfair.className} text-[clamp(2.2rem,8.5dvh,9rem)] font-semibold uppercase max-sm:text-[clamp(1.5rem,5.5dvh,2.4rem)]`}
          style={{
            lineHeight: "0.92",
            letterSpacing: "-0.02em",
            color: "#f6efe2",
          }}
        >
          {slide.titleLines.map((line, i) => (
            <span key={i} className="block">
              {line}
            </span>
          ))}
        </h2>

        <div className="flex flex-col gap-1.5 text-[10px] font-medium uppercase tracking-[0.32em] text-white/70 max-sm:text-[8.5px] max-sm:tracking-[0.22em]">
          <div className="flex items-baseline gap-3 max-sm:gap-2">
            <span className="text-white/45">DIRECTOR</span>
            <span className="text-white/90">{slide.director}</span>
          </div>
          <div className="flex items-baseline gap-3 max-sm:gap-2">
            <span className="text-white/45">CATEGORY</span>
            <span className="text-white/90">{slide.category}</span>
          </div>
        </div>
      </div>

      {/* C. RIGHT — award stack */}
      <div
        className="absolute right-[6dvh] top-1/2 flex flex-col max-sm:hidden"
        style={{ transform: "translateY(-50%)" }}
      >
        <div className="flex flex-col gap-7" data-reveal>
          {slide.awards.map((a, i) => (
            <div key={i} className="flex flex-col items-end gap-1.5 text-right">
              <div className="flex items-center gap-1">
                {Array.from({ length: 5 }).map((_, s) => (
                  <span
                    key={s}
                    className="text-[12px]"
                    style={{
                      color:
                        s < a.stars ? "#f1e7d2" : "rgba(255,255,255,0.18)",
                    }}
                  >
                    ★
                  </span>
                ))}
              </div>
              <div className="text-[9.5px] font-medium uppercase tracking-[0.32em] text-white/55">
                {a.label}
              </div>
              <div
                className={`${playfair.className} text-[16px] leading-tight text-white/95`}
                style={{ fontStyle: "italic", maxWidth: "16ch" }}
              >
                &ldquo;{a.quote}&rdquo;
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* D. EXPLORE button */}
      <button
        type="button"
        data-no-drag
        className="group absolute bottom-[5dvh] right-[6dvh] flex items-center gap-4 overflow-hidden rounded-full border border-white/35 bg-white/[0.04] px-8 py-4 text-[12px] font-medium uppercase tracking-[0.32em] text-white/95 backdrop-blur-md transition-[background-color,border-color,transform,box-shadow] duration-300 ease-out hover:scale-[1.04] hover:border-white/85 hover:bg-white/[0.14] hover:shadow-[0_10px_30px_rgba(0,0,0,0.45)] max-sm:bottom-[3dvh] max-sm:right-[3dvh] max-sm:gap-3 max-sm:px-5 max-sm:py-3 max-sm:text-[10.5px] max-sm:tracking-[0.24em]"
        style={{ cursor: "pointer" }}
        data-reveal
        onClick={(e) => {
          e.stopPropagation();
          onExplore();
        }}
      >
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0 -translate-x-full rounded-full bg-gradient-to-r from-white/[0.02] via-white/10 to-white/[0.02] transition-transform duration-500 ease-out group-hover:translate-x-0"
        />
        <span className="relative">EXPLORE</span>
        <span
          aria-hidden
          className="relative text-[15px] leading-none transition-transform duration-300 ease-out group-hover:translate-x-1.5 max-sm:text-[13px]"
        >
          →
        </span>
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   ReelIndicator
   ═══════════════════════════════════════════════════════════════════ */
function ReelIndicator({
  activeIdx,
  total,
  font,
  onPipClick,
  hidden,
}: {
  activeIdx: number;
  total: number;
  font: string;
  onPipClick: (i: number) => void;
  hidden: boolean;
}) {
  return (
    <div
      className={`absolute right-[3.5dvh] top-1/2 z-40 flex flex-col items-end gap-3 transition-opacity duration-[400ms] ease-out ${
        hidden ? "pointer-events-none opacity-0" : "pointer-events-none opacity-100"
      }`}
      style={{ transform: "translateY(-50%)" }}
      aria-hidden={hidden}
    >
      <div className={`${font} text-[12px] italic text-white/55`}>
        {String(activeIdx + 1).padStart(2, "0")}
      </div>

      <div
        data-no-drag
        className="pointer-events-auto flex flex-col items-center"
      >
        {Array.from({ length: total }).map((_, i) => {
          const active = i === activeIdx;
          return (
            <button
              key={i}
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onPipClick(i);
              }}
              aria-label={`Go to slide ${i + 1}`}
              className="flex h-5 w-5 items-center justify-center"
              style={{ cursor: "pointer" }}
            >
              <span
                className="rounded-full"
                style={{
                  width: active ? 6 : 4,
                  height: active ? 6 : 4,
                  background: active
                    ? "rgba(241,231,210,0.95)"
                    : "rgba(255,255,255,0.22)",
                  transition: "all 320ms cubic-bezier(0.16, 1, 0.3, 1)",
                }}
              />
            </button>
          );
        })}
      </div>

      <div className={`${font} text-[12px] italic text-white/35`}>
        {String(total).padStart(2, "0")}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   DetailsPanel
   ═══════════════════════════════════════════════════════════════════ */
function DetailsPanel({
  open,
  slide,
  imgDims,
  onClose,
}: {
  open: boolean;
  slide: Slide | null;
  imgDims: { w: number; h: number };
  onClose: () => void;
}) {
  return (
    <>
      {/* Backdrop */}
      <div
        data-no-drag
        aria-hidden={!open}
        onClick={onClose}
        className={`absolute z-40 ${
          open ? "pointer-events-auto" : "pointer-events-none"
        }`}
        style={{
          top: `${TOP_PAD_VH}dvh`,
          height: `${SLIDE_VH}dvh`,
          left: "var(--cinema-pad-x)",
          right: "var(--cinema-pad-x)",
          borderRadius: "48px",
          overflow: "hidden",
          backgroundColor: open ? "rgba(10,9,8,0.35)" : "rgba(10,9,8,0)",
          backdropFilter: open ? "blur(14px) saturate(120%)" : "blur(0px)",
          WebkitBackdropFilter: open ? "blur(14px) saturate(120%)" : "blur(0px)",
          transition:
            "background-color 600ms cubic-bezier(0.22, 1, 0.36, 1), " +
            "backdrop-filter 600ms cubic-bezier(0.22, 1, 0.36, 1), " +
            "-webkit-backdrop-filter 600ms cubic-bezier(0.22, 1, 0.36, 1)",
        }}
      />

      {/* Aside */}
      <aside
        data-no-drag
        aria-hidden={!open}
        className="absolute z-50 flex w-[min(640px,52%)] flex-col text-white max-sm:w-[calc(100vw-2*var(--cinema-pad-x))]"
        style={{
          top: `${TOP_PAD_VH}dvh`,
          height: `${SLIDE_VH}dvh`,
          right: "var(--cinema-pad-x)",
          borderRadius: "48px",
          overflow: "hidden",
          transform: open
            ? "translateX(0)"
            : "translateX(calc(100% + var(--cinema-pad-x) + 2dvh))",
          transition: "transform 700ms cubic-bezier(0.22, 1, 0.36, 1)",
          background:
            "linear-gradient(180deg, rgba(18,16,14,0.85) 0%, rgba(10,9,8,0.92) 100%)",
          backdropFilter: "blur(20px) saturate(140%)",
          WebkitBackdropFilter: "blur(20px) saturate(140%)",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow: open ? "-30px 0 80px -20px rgba(0,0,0,0.6)" : "none",
          willChange: "transform",
        }}
      >
        {slide && (
          <>
            <div
              className="h-full w-full overflow-y-auto"
              style={{ overscrollBehavior: "contain", touchAction: "pan-y" }}
            >
              {/* Hero image */}
              <div
                className="relative w-full overflow-hidden"
                style={{ height: "35dvh", flexShrink: 0 }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={imgUrl(
                    slide.imageId,
                    imgDims.w,
                    Math.round(imgDims.h * 0.6),
                    80,
                  )}
                  alt=""
                  draggable={false}
                  className="absolute inset-0 h-full w-full"
                  style={{ objectFit: "cover" }}
                />
                <div
                  className="absolute inset-x-0 bottom-0 h-1/2"
                  style={{
                    background:
                      "linear-gradient(180deg, " +
                      "rgba(10,9,8,0) 0%, rgba(10,9,8,0.85) 80%, rgba(10,9,8,1) 100%)",
                  }}
                />
              </div>

              {/* Body */}
              <div className="px-[3.5dvh] pb-[4dvh] pt-[1dvh]">
                <div className="text-[10px] font-medium uppercase tracking-[0.36em] text-white/55">
                  {slide.eyebrow}
                </div>

                <h2
                  className={`${playfair.className} mt-3 font-semibold uppercase`}
                  style={{
                    fontSize: "clamp(2.2rem, 4.6dvh, 4rem)",
                    lineHeight: 0.95,
                    letterSpacing: "-0.015em",
                    color: "#f6efe2",
                  }}
                >
                  {slide.titleLines.map((line, i) => (
                    <span key={i} className="block">
                      {line}
                    </span>
                  ))}
                </h2>

                <div className="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-1 text-[10.5px] font-medium uppercase tracking-[0.32em] text-white/75">
                  <span>
                    <span className="text-white/45">DIR.</span>{" "}
                    <span className="text-white/95">{slide.director}</span>
                  </span>
                  <span className="text-white/30">·</span>
                  <span className="text-white/95">{slide.year}</span>
                  <span className="text-white/30">·</span>
                  <span className="text-white/75">{slide.category}</span>
                </div>

                <div className="my-6 h-px w-full bg-white/10" />

                <p
                  className={`${playfair.className} text-[15.5px] leading-[1.65] text-white/85`}
                  style={{ fontStyle: "italic" }}
                >
                  {slide.description}
                </p>

                <div className="my-6 h-px w-full bg-white/10" />

                <div className="grid grid-cols-3 gap-x-5 gap-y-5">
                  <Stat label="CRITICS" value={`${slide.stats.critics}`} suffix="%" />
                  <Stat label="AUDIENCE" value={`${slide.stats.audience}`} suffix="%" />
                  <Stat label="RUNTIME" value={slide.stats.runtime} />
                  <Stat label="FORMAT" value={slide.stats.format} />
                  <Stat label="ASPECT" value={slide.stats.aspect} />
                  <Stat label="LANGUAGE" value={slide.stats.language} />
                </div>
                <div className="mt-5 grid grid-cols-1">
                  <Stat label="COUNTRY" value={slide.stats.country} />
                </div>

                <div className="my-6 h-px w-full bg-white/10" />

                <div className="flex flex-col gap-3">
                  {slide.awards.map((a, i) => (
                    <div key={i} className="flex items-baseline gap-3">
                      <div className="flex shrink-0 items-center gap-[2px]">
                        {Array.from({ length: 5 }).map((_, s) => (
                          <span
                            key={s}
                            className="text-[11px]"
                            style={{
                              color:
                                s < a.stars
                                  ? "#f1e7d2"
                                  : "rgba(255,255,255,0.18)",
                            }}
                          >
                            ★
                          </span>
                        ))}
                      </div>
                      <div className="shrink-0 text-[10px] font-medium uppercase tracking-[0.32em] text-white/55">
                        {a.label}
                      </div>
                      <div
                        className={`${playfair.className} flex-1 text-[13px] leading-tight text-white/90`}
                        style={{ fontStyle: "italic" }}
                      >
                        &ldquo;{a.quote}&rdquo;
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              aria-label="Close details"
              className="absolute right-[3dvh] top-[3dvh] z-10 flex h-10 w-10 items-center justify-center rounded-full border border-white/30 bg-black/40 text-white/85 backdrop-blur-md transition-colors hover:bg-black/60"
              style={{ cursor: "pointer" }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden>
                <path
                  d="M1 1L13 13M13 1L1 13"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </>
        )}
      </aside>
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   Stat
   ═══════════════════════════════════════════════════════════════════ */
function Stat({
  label,
  value,
  suffix,
}: {
  label: string;
  value: string;
  suffix?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="text-[9.5px] font-medium uppercase tracking-[0.32em] text-white/45">
        {label}
      </div>
      <div className={`${playfair.className} text-[20px] leading-none text-white/95`}>
        {value}
        {suffix && (
          <span className="ml-0.5 text-[11px] text-white/55">{suffix}</span>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   Cursor glyphs
   ═══════════════════════════════════════════════════════════════════ */
function GrabHand() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="white"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M7 11V7.5a1.5 1.5 0 0 1 3 0V11" />
      <path d="M10 11V6.5a1.5 1.5 0 0 1 3 0V11" />
      <path d="M13 11V7a1.5 1.5 0 0 1 3 0v6" />
      <path d="M16 9.5a1.5 1.5 0 0 1 3 0V15c0 3-2.2 6-6 6-3.4 0-5.5-1.8-6.5-3.5l-2.7-4.7a1.4 1.4 0 0 1 2.4-1.4L8 13" />
    </svg>
  );
}

function ChevronGlyph() {
  return (
    <svg width="22" height="14" viewBox="0 0 22 14" fill="none" aria-hidden>
      <path
        d="M2 12 C 7 4, 15 4, 20 12"
        stroke="white"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}
