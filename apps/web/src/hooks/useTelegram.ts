'use client';

import { useEffect, useState } from 'react';
import { getWebApp } from '@/lib/telegram';
import type { TelegramWebAppUser } from '@/types/telegram';

interface UseTelegramResult {
  ready: boolean;
  user: TelegramWebAppUser | null;
  /** True when running inside the Telegram client. */
  inTelegram: boolean;
}

/**
 * Initializes the Telegram WebApp SDK on mount: marks the app as ready and
 * expands it to full height. The LumiPic look intentionally uses a fixed dark
 * palette rather than the user's Telegram theme, so we do not sync theme params.
 */
export function useTelegram(): UseTelegramResult {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<TelegramWebAppUser | null>(null);
  const [inTelegram, setInTelegram] = useState(false);

  useEffect(() => {
    const webApp = getWebApp();
    if (!webApp) {
      setReady(true);
      return;
    }

    setInTelegram(true);
    webApp.ready();
    webApp.expand();
    setUser(webApp.initDataUnsafe.user ?? null);
    setReady(true);
  }, []);

  return { ready, user, inTelegram };
}
