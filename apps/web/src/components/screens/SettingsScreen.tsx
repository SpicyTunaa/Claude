'use client';

import { LifeBuoy } from 'lucide-react';
import { ContentCard } from '@/components/ui/ContentCard';
import type { TelegramWebAppUser } from '@/types/telegram';

interface SettingsScreenProps {
  user: TelegramWebAppUser | null;
  gems: number;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-surfaceLine py-3 last:border-0">
      <span className="text-sm text-secondaryText">{label}</span>
      <span className="text-sm font-medium text-primaryText">{value}</span>
    </div>
  );
}

export function SettingsScreen({ user, gems }: SettingsScreenProps) {
  const fullName = user
    ? [user.first_name, user.last_name].filter(Boolean).join(' ')
    : 'Guest';

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-primaryText">Settings</h1>

      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center overflow-hidden rounded-full bg-surface text-lg font-bold text-primaryText">
          {user?.photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={user.photo_url} alt="" className="h-full w-full object-cover" />
          ) : (
            fullName.charAt(0).toUpperCase()
          )}
        </div>
        <div>
          <p className="text-lg font-bold text-primaryText">{fullName}</p>
          {user?.username && (
            <p className="text-sm text-secondaryText">@{user.username}</p>
          )}
        </div>
      </div>

      <ContentCard className="mb-4">
        <Row label="User ID" value={user ? String(user.id) : '—'} />
        <Row label="Language" value={user?.language_code?.toUpperCase() ?? '—'} />
        <Row label="Telegram Premium" value={user?.is_premium ? 'Yes' : 'No'} />
        <Row label="Gem balance" value={String(gems)} />
      </ContentCard>

      <button
        type="button"
        className="flex w-full items-center justify-center gap-2 rounded-button bg-premium py-3.5 text-base font-bold text-black transition active:scale-[0.99]"
      >
        <LifeBuoy className="h-5 w-5" /> Contact Support
      </button>
    </div>
  );
}
