'use client';

import { useState } from 'react';
import { ImagePicker } from '@/components/ImagePicker';
import { useTelegram } from '@/hooks/useTelegram';
import { requestFaceSwap } from '@/lib/api';
import { getWebApp } from '@/lib/telegram';

type Status = 'idle' | 'loading' | 'done' | 'error';

export function FaceSwapApp() {
  const { ready, user, inTelegram } = useTelegram();
  const [source, setSource] = useState<File | null>(null);
  const [target, setTarget] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = !!source && status !== 'loading';

  async function handleSubmit() {
    if (!source) return;
    setStatus('loading');
    setError(null);
    setResult(null);
    getWebApp()?.HapticFeedback?.impactOccurred('light');

    try {
      const res = await requestFaceSwap({
        source,
        target: target ?? undefined,
        prompt: prompt.trim() || undefined,
      });
      setResult(res.imageUrl);
      setStatus('done');
      getWebApp()?.HapticFeedback?.notificationOccurred('success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong';
      setError(message);
      setStatus('error');
      getWebApp()?.HapticFeedback?.notificationOccurred('error');
    }
  }

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center text-tg-hint">
        Loading…
      </div>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col gap-5 p-4">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tg-text">LumiPic Face Swap</h1>
        <p className="text-sm text-tg-hint">
          {user
            ? `Hi ${user.first_name ?? 'there'}, upload a selfie to get started.`
            : 'Upload a selfie to get started.'}
        </p>
      </header>

      {!inTelegram && (
        <div className="rounded-xl bg-yellow-100 p-3 text-sm text-yellow-900">
          Running outside Telegram — authentication will be rejected unless the
          server has <code>ALLOW_INSECURE_AUTH=true</code>.
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <ImagePicker label="Your face" file={source} onSelect={setSource} />
        <ImagePicker
          label="Template"
          file={target}
          onSelect={setTarget}
          optional
        />
      </div>

      <label className="flex flex-col gap-2">
        <span className="text-sm font-medium text-tg-text">Prompt</span>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. astronaut on the moon, cinematic lighting"
          rows={3}
          className="resize-none rounded-xl border border-tg-hint/30 bg-tg-secondaryBg p-3 text-sm text-tg-text outline-none focus:border-tg-link"
        />
      </label>

      <button
        type="button"
        disabled={!canSubmit}
        onClick={handleSubmit}
        className="rounded-xl bg-tg-button py-3 font-semibold text-tg-buttonText transition active:scale-[0.99] disabled:opacity-50"
      >
        {status === 'loading' ? 'Generating…' : 'Swap face'}
      </button>

      {error && (
        <p className="rounded-xl bg-red-100 p-3 text-sm text-red-800">{error}</p>
      )}

      {result && (
        <section className="flex flex-col gap-2">
          <h2 className="text-sm font-medium text-tg-text">Result</h2>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={result}
            alt="Face swap result"
            className="w-full rounded-2xl"
          />
          <a
            href={result}
            download="lumipic-result.png"
            className="self-start text-sm text-tg-link"
          >
            Download
          </a>
        </section>
      )}
    </main>
  );
}
