export type SectionCategory =
  | "hero"
  | "portfolio"
  | "gallery"
  | "feature"
  | "pricing"
  | "footer";

export type SectionTier = "standard" | "premium" | "exceptional";

export type EmotionalRegister =
  | "dramatic"
  | "elegant"
  | "immersive"
  | "playful"
  | "minimal"
  | "energetic";

export interface SectionEntry {
  slug: string;
  title: string;
  description: string;
  category: SectionCategory;
  tier: SectionTier;
  emotionalRegister: EmotionalRegister[];
  priceCents: number;
}

export const SECTION_REGISTRY: SectionEntry[] = [
  {
    slug: "cinema-reel",
    title: "Cinema Reel",
    description:
      "A vertical film-portfolio slider with cinematic snap-physics. Six framed reels load with a motion-blurred fast-forward, then settle into a spring-snapped scroller with parallax frames, a custom cursor, and a 3D-tilt detail modal.",
    category: "portfolio",
    tier: "exceptional",
    emotionalRegister: ["dramatic", "elegant", "immersive"],
    priceCents: 24900,
  },
];

export function getSection(slug: string): SectionEntry | undefined {
  return SECTION_REGISTRY.find((s) => s.slug === slug);
}
