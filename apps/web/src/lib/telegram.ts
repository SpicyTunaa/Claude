import type { TelegramWebApp } from '@/types/telegram';

/** Returns the Telegram WebApp instance, or null when running outside Telegram. */
export function getWebApp(): TelegramWebApp | null {
  if (typeof window === 'undefined') return null;
  return window.Telegram?.WebApp ?? null;
}
