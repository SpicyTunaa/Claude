import { SECTION_COMPONENTS } from "@/lib/sections/components";

export default function Home() {
  const CinemaReel = SECTION_COMPONENTS["cinema-reel"];
  return (
    <main>
      <CinemaReel />
    </main>
  );
}
