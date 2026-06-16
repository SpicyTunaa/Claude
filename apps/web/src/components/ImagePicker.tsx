'use client';

import { useRef } from 'react';

interface ImagePickerProps {
  label: string;
  file: File | null;
  onSelect: (file: File | null) => void;
  optional?: boolean;
}

export function ImagePicker({ label, file, onSelect, optional }: ImagePickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const previewUrl = file ? URL.createObjectURL(file) : null;

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-medium text-tg-text">
        {label}
        {optional && <span className="text-tg-hint"> (optional)</span>}
      </span>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="relative flex aspect-square w-full items-center justify-center overflow-hidden rounded-2xl border-2 border-dashed border-tg-hint/40 bg-tg-secondaryBg transition active:scale-[0.99]"
      >
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={previewUrl}
            alt={label}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="px-4 text-center text-sm text-tg-hint">
            Tap to choose a photo
          </span>
        )}
      </button>

      {file && (
        <button
          type="button"
          onClick={() => onSelect(null)}
          className="self-start text-xs text-tg-link"
        >
          Remove
        </button>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={(e) => onSelect(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}
