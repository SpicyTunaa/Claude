import dynamic from "next/dynamic";
import type { ComponentType } from "react";

export interface SectionComponentProps {
  className?: string;
}

export const SECTION_COMPONENTS: Record<
  string,
  ComponentType<SectionComponentProps>
> = {
  "cinema-reel": dynamic(
    () => import("@/components/sections/cinema-reel/CinemaReel"),
  ),
};
