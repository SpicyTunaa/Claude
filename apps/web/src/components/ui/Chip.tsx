'use client';

import type { ReactNode } from 'react';

interface ChipProps {
  label: ReactNode;
  active?: boolean;
  onClick?: () => void;
}

/** Bordered rounded selection chip (e.g. gender options). */
export function Chip({ label, active = false, onClick }: ChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-pill border px-4 py-2 text-sm font-medium transition active:scale-95 ${
        active
          ? 'border-transparent bg-accentBlue text-primaryText'
          : 'border-surfaceLine bg-surfaceAlt text-secondaryText'
      }`}
    >
      {label}
    </button>
  );
}
