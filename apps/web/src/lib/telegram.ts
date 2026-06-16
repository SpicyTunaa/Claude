import type { TelegramThemeParams, TelegramWebApp } from '@/types/telegram';

/** Returns the Telegram WebApp instance, or null when running outside Telegram. */
export function getWebApp(): TelegramWebApp | null {
  if (typeof window === 'undefined') return null;
  return window.Telegram?.WebApp ?? null;
}

/** Applies Telegram theme params to CSS custom properties on :root. */
export function applyThemeParams(params: TelegramThemeParams): void {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const map: Record<keyof TelegramThemeParams, string> = {
    bg_color: '--tg-theme-bg-color',
    text_color: '--tg-theme-text-color',
    hint_color: '--tg-theme-hint-color',
    link_color: '--tg-theme-link-color',
    button_color: '--tg-theme-button-color',
    button_text_color: '--tg-theme-button-text-color',
    secondary_bg_color: '--tg-theme-secondary-bg-color',
  };
  for (const [key, cssVar] of Object.entries(map) as [
    keyof TelegramThemeParams,
    string,
  ][]) {
    const value = params[key];
    if (value) root.style.setProperty(cssVar, value);
  }
}
