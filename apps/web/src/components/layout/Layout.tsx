'use client';

import type { ReactNode } from 'react';
import { BottomNav } from './BottomNav';
import { Header } from './Header';
import type { ScreenId } from '@/types/navigation';

interface LayoutProps {
  title: string;
  active: ScreenId;
  gems: number;
  onNavigate: (id: ScreenId) => void;
  children: ReactNode;
}

/**
 * Three-layer app shell: a fixed header, a scrollable content area, and a fixed
 * bottom navigation. Screens that need a sticky CTA render their own StickyBar.
 */
export function Layout({
  title,
  active,
  gems,
  onNavigate,
  children,
}: LayoutProps) {
  return (
    <div className="min-h-screen bg-primaryBg">
      <Header title={title} gems={gems} />

      <main
        className="mx-auto w-full max-w-md px-4 pb-24"
        style={{ paddingTop: 'calc(var(--safe-top) + 72px)' }}
      >
        {children}
      </main>

      <BottomNav active={active} onNavigate={onNavigate} />
    </div>
  );
}
