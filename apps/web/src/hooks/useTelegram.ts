'use client';

import { useEffect, useState } from 'react';
import { applyThemeParams, getWebApp } from '@/lib/telegram';
import type { TelegramWebAppUser } from '@/types/telegram';

interface UseTelegramResult {
  ready: boolean;
  user: TelegramWebAppUser | null;
  colorScheme: 'light' | 'dark';
  /** True when running inside the Telegram client. */
  inTelegram: boolean;
}

/**
 * Initializes the Telegram WebApp SDK on mount: marks the app as ready,
 * expands it to full height, syncs theme params, and tracks theme changes.
 */
export function useTelegram(): UseTelegramResult {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<TelegramWebAppUser | null>(null);
  const [colorScheme, setColorScheme] = useState<'light' | 'dark'>('light');
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
    applyThemeParams(webApp.themeParams);
    setColorScheme(webApp.colorScheme);
    setUser(webApp.initDataUnsafe.user ?? null);
    setReady(true);

    const handleThemeChange = () => {
      applyThemeParams(webApp.themeParams);
      setColorScheme(webApp.colorScheme);
    };
    webApp.onEvent('themeChanged', handleThemeChange);
    return () => webApp.offEvent('themeChanged', handleThemeChange);
  }, []);

  return { ready, user, colorScheme, inTelegram };
}
