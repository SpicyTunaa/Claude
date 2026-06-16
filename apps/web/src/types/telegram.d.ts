// Minimal typings for the Telegram WebApp JS bridge.
// Full reference: https://core.telegram.org/bots/webapps#initializing-mini-apps

export interface TelegramWebAppUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
  is_premium?: boolean;
}

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

export interface TelegramBackButton {
  isVisible: boolean;
  show(): void;
  hide(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
}

export interface TelegramMainButton {
  text: string;
  isVisible: boolean;
  isActive: boolean;
  showProgress(leaveActive?: boolean): void;
  hideProgress(): void;
  setText(text: string): void;
  show(): void;
  hide(): void;
  enable(): void;
  disable(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
}

export interface TelegramPopupButton {
  id?: string;
  type?: 'default' | 'ok' | 'close' | 'cancel' | 'destructive';
  text?: string;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: TelegramWebAppUser;
    auth_date?: number;
    hash?: string;
    query_id?: string;
  };
  colorScheme: 'light' | 'dark';
  themeParams: TelegramThemeParams;
  isExpanded: boolean;
  version: string;
  platform: string;
  BackButton: TelegramBackButton;
  MainButton: TelegramMainButton;
  ready(): void;
  expand(): void;
  close(): void;
  showPopup(
    params: { title?: string; message: string; buttons?: TelegramPopupButton[] },
    callback?: (buttonId: string) => void,
  ): void;
  showAlert(message: string, callback?: () => void): void;
  HapticFeedback?: {
    impactOccurred(style: 'light' | 'medium' | 'heavy'): void;
    notificationOccurred(type: 'error' | 'success' | 'warning'): void;
  };
  onEvent(event: string, handler: () => void): void;
  offEvent(event: string, handler: () => void): void;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export {};
