'use client';

import { Sparkles } from 'lucide-react';
import { GalleryCard } from '@/components/ui/GalleryCard';
import type { GalleryItem } from '@/types/navigation';

interface GalleryScreenProps {
  items: GalleryItem[];
  onCreate: () => void;
}

export function GalleryScreen({ items, onCreate }: GalleryScreenProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
        <span className="flex h-20 w-20 items-center justify-center rounded-full bg-surface">
          <Sparkles className="h-9 w-9 text-secondaryText" />
        </span>
        <h2 className="text-xl font-bold text-primaryText">No creations yet</h2>
        <p className="max-w-xs text-sm text-secondaryText">
          Upload a selfie and generate your first AI face swap to see it here.
        </p>
        <button
          type="button"
          onClick={onCreate}
          className="mt-2 flex items-center gap-2 rounded-pill bg-primaryText px-6 py-3 text-sm font-bold text-primaryBg transition active:scale-95"
        >
          <Sparkles className="h-4 w-4" /> Create now
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-primaryText">Gallery</h1>
      {items.map((item) => (
        <GalleryCard key={item.id} item={item} />
      ))}
    </div>
  );
}
