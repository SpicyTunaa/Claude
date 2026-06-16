'use client';

import { Gem, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { StickyBar } from '@/components/layout/StickyBar';
import { Chip } from '@/components/ui/Chip';
import { ContentCard } from '@/components/ui/ContentCard';
import { ImageUpload } from '@/components/ui/ImageUpload';
import { PrimaryButton } from '@/components/ui/PrimaryButton';
import { Stepper } from '@/components/ui/Stepper';
import { requestFaceSwap } from '@/lib/api';
import { getWebApp } from '@/lib/telegram';
import type { GalleryItem } from '@/types/navigation';

const CATEGORIES = ['Looks', 'Clothes', 'Action', 'Environment', 'Camera'];
const GENDERS = ['Female', 'Male', 'Any'];
const GEMS_PER_IMAGE = 10;

interface CreateScreenProps {
  onGenerated: (items: GalleryItem[]) => void;
  /** Spend gems; returns false when the balance is insufficient. */
  onSpend: (amount: number) => boolean;
  onError: (message: string) => void;
  setBusy: (message: string | null) => void;
}

export function CreateScreen({
  onGenerated,
  onSpend,
  onError,
  setBusy,
}: CreateScreenProps) {
  const [photos, setPhotos] = useState<File[]>([]);
  const [template, setTemplate] = useState<File[]>([]);
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [gender, setGender] = useState(GENDERS[0]);
  const [prompt, setPrompt] = useState('');
  const [count, setCount] = useState(1);

  const cost = count * GEMS_PER_IMAGE;
  const canSubmit = photos.length > 0;

  // Compose a prompt from the structured selections plus free text.
  const composedPrompt = () =>
    [prompt.trim(), category, gender !== 'Any' ? gender : '']
      .filter(Boolean)
      .join(', ');

  async function handleGenerate() {
    if (!canSubmit) return;
    if (!onSpend(cost)) {
      onError('Not enough gems. Visit the Shop to top up.');
      return;
    }

    getWebApp()?.HapticFeedback?.impactOccurred('light');
    setBusy('Generating your photos…');
    try {
      const source = photos[0];
      const target = template[0];
      const finalPrompt = composedPrompt();

      const results: GalleryItem[] = [];
      for (let i = 0; i < count; i++) {
        const res = await requestFaceSwap({
          source,
          target,
          prompt: finalPrompt || undefined,
        });
        results.push({
          id: `${Date.now()}-${i}`,
          sourceUrl: URL.createObjectURL(source),
          resultUrl: res.imageUrl,
          prompt: finalPrompt || undefined,
          createdAt: Date.now(),
        });
      }

      onGenerated(results);
      getWebApp()?.HapticFeedback?.notificationOccurred('success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Generation failed';
      onError(message);
      getWebApp()?.HapticFeedback?.notificationOccurred('error');
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="pb-28">
      <h1 className="mb-1 text-2xl font-bold text-primaryText">Create</h1>
      <p className="mb-5 text-sm text-secondaryText">
        Upload a clear selfie and describe the look you want.
      </p>

      <div className="flex flex-col gap-4">
        <ImageUpload
          title="Upload up to 5 Photos"
          subtitle="All pictures must show the same person."
          files={photos}
          maxFiles={5}
          onChange={setPhotos}
        />

        <ImageUpload
          title="Template (optional)"
          subtitle="Swap your face onto this image."
          files={template}
          maxFiles={1}
          onChange={setTemplate}
        />

        <div className="flex gap-2 overflow-x-auto pb-1">
          {CATEGORIES.map((c) => (
            <Chip
              key={c}
              label={c}
              active={c === category}
              onClick={() => setCategory(c)}
            />
          ))}
        </div>

        <ContentCard>
          <span className="mb-3 block text-sm font-semibold text-primaryText">
            Gender
          </span>
          <div className="flex gap-2">
            {GENDERS.map((g) => (
              <Chip
                key={g}
                label={g}
                active={g === gender}
                onClick={() => setGender(g)}
              />
            ))}
          </div>
        </ContentCard>

        <ContentCard>
          <span className="mb-2 block text-sm font-semibold text-primaryText">
            Prompt
          </span>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
            placeholder="e.g. cinematic portrait, golden hour, film grain"
            className="w-full resize-none rounded-xl border border-surfaceLine bg-surfaceAlt p-3 text-sm text-primaryText outline-none placeholder:text-mutedText focus:border-accentBlue"
          />
        </ContentCard>

        <ContentCard className="flex items-center justify-between">
          <span className="text-sm font-semibold text-primaryText">
            Number of photos
          </span>
          <Stepper value={count} min={1} max={4} onChange={setCount} />
        </ContentCard>
      </div>

      <StickyBar>
        <PrimaryButton
          onClick={handleGenerate}
          disabled={!canSubmit}
          trailing={
            <span className="flex items-center gap-1 rounded-full bg-black/20 px-2 py-0.5 text-sm">
              <Gem className="h-3.5 w-3.5" /> {cost}
            </span>
          }
        >
          <span className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" /> Generate
          </span>
        </PrimaryButton>
      </StickyBar>
    </div>
  );
}
