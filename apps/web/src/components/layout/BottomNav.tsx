'use client';

import { Images, Settings, Sparkles, Store } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { ScreenId } from '@/types/navigation';

const ITEMS: { id: ScreenId; label: string; icon: LucideIcon }[] = [
  { id: 'gallery', label: 'Gallery', icon: Images },
  { id: 'create', label: 'Create', icon: Sparkles },
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'shop', label: 'Shop', icon: Store },
];

interface BottomNavProps {
  active: ScreenId;
  onNavigate: (id: ScreenId) => void;
}

/** Sticky bottom navigation; the active item sits in a highlighted blue tile. */
export function BottomNav({ active, onNavigate }: BottomNavProps) {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-20 border-t border-surfaceLine bg-surface/95 backdrop-blur"
      style={{ paddingBottom: 'calc(var(--safe-bottom) + 8px)' }}
    >
      <div className="mx-auto flex max-w-md items-center justify-around px-2 pt-2">
        {ITEMS.map(({ id, label, icon: Icon }) => {
          const isActive = id === active;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onNavigate(id)}
              className={`flex flex-col items-center gap-1 rounded-button px-4 py-1.5 transition ${
                isActive ? 'bg-accentBlue text-primaryText' : 'text-secondaryText'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="text-[11px] font-medium">{label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
