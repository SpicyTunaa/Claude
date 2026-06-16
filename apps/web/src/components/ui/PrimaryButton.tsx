'use client';

import type { ReactNode } from 'react';

interface PrimaryButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  /** Optional inline trailing content, e.g. a gem cost badge. */
  trailing?: ReactNode;
}

/** Large, full-width muted-blue CTA used at the bottom of most screens. */
export function PrimaryButton({
  children,
  onClick,
  disabled = false,
  trailing,
}: PrimaryButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="flex h-14 w-full items-center justify-center gap-2 rounded-button bg-cta text-base font-bold text-primaryText transition active:scale-[0.99] enabled:hover:bg-ctaHover disabled:cursor-not-allowed disabled:opacity-40"
    >
      <span>{children}</span>
      {trailing}
    </button>
  );
}
