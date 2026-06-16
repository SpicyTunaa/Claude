'use client';

import { ChevronLeft, Gem } from 'lucide-react';

interface HeaderProps {
  title: string;
  /** When provided, a left back pill is shown. */
  onBack?: () => void;
  gems: number;
}

/** Floating top control row: left back/title pill and a right gem-balance pill. */
export function Header({ title, onBack, gems }: HeaderProps) {
  return (
    <header
      className="fixed inset-x-0 top-0 z-20 flex items-center justify-between px-4 pb-2"
      style={{ paddingTop: 'calc(var(--safe-top) + 12px)' }}
    >
      {onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 rounded-pill bg-surface/80 py-2 pl-2 pr-4 text-sm font-semibold text-primaryText backdrop-blur"
        >
          <ChevronLeft className="h-5 w-5" />
          Back
        </button>
      ) : (
        <span className="rounded-pill bg-surface/80 px-4 py-2 text-sm font-semibold text-primaryText backdrop-blur">
          {title}
        </span>
      )}

      <span className="flex items-center gap-1.5 rounded-pill bg-surface/80 px-4 py-2 text-sm font-semibold text-primaryText backdrop-blur">
        <Gem className="h-4 w-4 text-accentBlue2" />
        {gems}
      </span>
    </header>
  );
}
