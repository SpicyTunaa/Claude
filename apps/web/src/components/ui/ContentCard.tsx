import type { ReactNode } from 'react';

interface ContentCardProps {
  children: ReactNode;
  className?: string;
}

/** Rounded dark surface with a thin subtle border — the base content card. */
export function ContentCard({ children, className = '' }: ContentCardProps) {
  return (
    <div
      className={`rounded-card border border-surfaceLine bg-surface p-4 shadow-card ${className}`}
    >
      {children}
    </div>
  );
}
