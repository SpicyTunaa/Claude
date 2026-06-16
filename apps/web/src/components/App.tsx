'use client';

import { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { CreateScreen } from '@/components/screens/CreateScreen';
import { GalleryScreen } from '@/components/screens/GalleryScreen';
import { SettingsScreen } from '@/components/screens/SettingsScreen';
import { ShopScreen } from '@/components/screens/ShopScreen';
import { LoadingOverlay } from '@/components/ui/LoadingOverlay';
import { useTelegram } from '@/hooks/useTelegram';
import { getWebApp } from '@/lib/telegram';
import type { GalleryItem, ScreenId } from '@/types/navigation';

const TITLES: Record<ScreenId, string> = {
  gallery: 'Gallery',
  create: 'Create',
  settings: 'Settings',
  shop: 'Shop',
};

export function App() {
  const { ready, user, inTelegram } = useTelegram();
  const [screen, setScreen] = useState<ScreenId>('create');
  const [gems, setGems] = useState(100);
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  function showError(message: string) {
    const webApp = getWebApp();
    if (webApp) webApp.showAlert(message);
    else window.alert(message);
  }

  function spend(amount: number): boolean {
    if (gems < amount) return false;
    setGems((g) => g - amount);
    return true;
  }

  function handleGenerated(newItems: GalleryItem[]) {
    setItems((prev) => [...newItems, ...prev]);
    setScreen('gallery');
  }

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-primaryBg text-secondaryText">
        Loading…
      </div>
    );
  }

  return (
    <>
      {busy && <LoadingOverlay message={busy} />}

      <Layout
        title={TITLES[screen]}
        active={screen}
        gems={gems}
        onNavigate={setScreen}
      >
        {!inTelegram && (
          <div className="mb-4 rounded-card border border-premium/40 bg-premium/10 p-3 text-xs text-premium">
            Running outside Telegram — set <code>ALLOW_INSECURE_AUTH=true</code>{' '}
            on the server to test generation in a browser.
          </div>
        )}

        {screen === 'create' && (
          <CreateScreen
            onGenerated={handleGenerated}
            onSpend={spend}
            onError={showError}
            setBusy={setBusy}
          />
        )}
        {screen === 'gallery' && (
          <GalleryScreen items={items} onCreate={() => setScreen('create')} />
        )}
        {screen === 'settings' && <SettingsScreen user={user} gems={gems} />}
        {screen === 'shop' && (
          <ShopScreen gems={gems} onPurchase={(amt) => setGems((g) => g + amt)} />
        )}
      </Layout>
    </>
  );
}
