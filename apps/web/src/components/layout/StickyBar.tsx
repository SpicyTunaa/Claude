'use client';

import type { ReactNode } from 'react';

interface StickyBarProps {
  children: ReactNode;
}

/**
 * Fixed action bar pinned just above the bottom navigation. Screens that use it
 * should add extra bottom padding (e.g. `pb-28`) so content isn't hidden.
 */
export function StickyBar({ children }: StickyBarProps) {
  return (
    <div
      className="fixed inset-x-0 z-20 mx-auto w-full max-w-md px-4"
      style={{ bottom: 'calc(var(--safe-bottom) + 80px)' }}
    >
      {children}
    </div>
  );
}
