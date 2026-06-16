'use client';

import { Download, Play } from 'lucide-react';
import type { GalleryItem } from '@/types/navigation';
import { ContentCard } from './ContentCard';

interface GalleryCardProps {
  item: GalleryItem;
}

/** Bundle card: selfie preview on the left, generated result on the right. */
export function GalleryCard({ item }: GalleryCardProps) {
  return (
    <ContentCard className="mb-4">
      <div className="mb-3 flex gap-2">
        <div className="relative aspect-square w-1/2 overflow-hidden rounded-xl">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={item.sourceUrl}
            alt="Your selfie"
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-2">
            <span className="text-[11px] font-bold tracking-wide text-primaryText">
              YOUR SELFIE
            </span>
          </div>
        </div>

        <div className="relative aspect-square w-1/2 overflow-hidden rounded-xl">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={item.resultUrl}
            alt="Generated result"
            className="h-full w-full object-cover"
          />
          <span className="absolute left-2 top-2 flex items-center gap-1 rounded-full bg-black/65 px-2 py-1 text-[10px] font-semibold text-primaryText">
            <Play className="h-3 w-3" /> RESULT
          </span>
        </div>
      </div>

      {item.prompt && (
        <p className="mb-3 line-clamp-2 text-sm text-secondaryText">
          {item.prompt}
        </p>
      )}

      <div className="flex items-center justify-between">
        <span className="text-xs text-mutedText">
          {new Date(item.createdAt).toLocaleString()}
        </span>
        <a
          href={item.resultUrl}
          download={`result-${item.id}.png`}
          className="flex items-center gap-1.5 rounded-pill bg-accentBlue px-4 py-2 text-sm font-bold text-primaryText transition active:scale-95"
        >
          <Download className="h-4 w-4" /> Save
        </a>
      </div>
    </ContentCard>
  );
}
