'use client';

import { ImagePlus, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface ImageUploadProps {
  title: string;
  subtitle?: string;
  files: File[];
  maxFiles?: number;
  onChange: (files: File[]) => void;
}

/**
 * Dashed rounded dropzone supporting multiple photos with thumbnail previews.
 * Mirrors the LumiPic "Upload up to N Photos" pattern.
 */
export function ImageUpload({
  title,
  subtitle,
  files,
  maxFiles = 5,
  onChange,
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<string[]>([]);

  // Recreate object URLs whenever the file list changes, and revoke on cleanup.
  useEffect(() => {
    const urls = files.map((f) => URL.createObjectURL(f));
    setPreviews(urls);
    return () => urls.forEach((u) => URL.revokeObjectURL(u));
  }, [files]);

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const next = [...files, ...Array.from(incoming)].slice(0, maxFiles);
    onChange(next);
  };

  const removeAt = (index: number) =>
    onChange(files.filter((_, i) => i !== index));

  return (
    <div className="rounded-card border border-dashed border-surfaceLine bg-surface p-5">
      {previews.length > 0 && (
        <div className="mb-4 grid grid-cols-3 gap-2">
          {previews.map((src, i) => (
            <div
              key={src}
              className="relative aspect-square overflow-hidden rounded-xl"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt="" className="h-full w-full object-cover" />
              <button
                type="button"
                aria-label="Remove photo"
                onClick={() => removeAt(i)}
                className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-primaryText"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={files.length >= maxFiles}
        className="flex w-full flex-col items-center gap-2 py-4 disabled:opacity-40"
      >
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-surfaceAlt">
          <ImagePlus className="h-7 w-7 text-secondaryText" />
        </span>
        <span className="text-base font-semibold text-primaryText">{title}</span>
        {subtitle && (
          <span className="text-center text-sm text-secondaryText">
            {subtitle}
          </span>
        )}
      </button>

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        multiple={maxFiles > 1}
        className="hidden"
        onChange={(e) => {
          addFiles(e.target.files);
          e.target.value = '';
        }}
      />
    </div>
  );
}
