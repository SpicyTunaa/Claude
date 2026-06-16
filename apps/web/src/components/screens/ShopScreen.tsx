'use client';

import { Gem } from 'lucide-react';
import { ContentCard } from '@/components/ui/ContentCard';

interface Pack {
  id: string;
  gems: number;
  price: string;
  bonus?: string;
  highlight?: boolean;
}

const PACKS: Pack[] = [
  { id: 'starter', gems: 50, price: '$4.99' },
  { id: 'popular', gems: 150, price: '$9.99', bonus: '+20 bonus', highlight: true },
  { id: 'pro', gems: 500, price: '$24.99', bonus: '+100 bonus' },
];

interface ShopScreenProps {
  gems: number;
  onPurchase: (amount: number) => void;
}

export function ShopScreen({ gems, onPurchase }: ShopScreenProps) {
  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold text-primaryText">Shop</h1>
      <p className="mb-5 flex items-center gap-1.5 text-sm text-secondaryText">
        Balance:
        <span className="flex items-center gap-1 font-semibold text-primaryText">
          <Gem className="h-4 w-4 text-accentBlue2" /> {gems}
        </span>
      </p>

      <div className="flex flex-col gap-3">
        {PACKS.map((pack) => (
          <ContentCard
            key={pack.id}
            className={`flex items-center justify-between ${
              pack.highlight ? 'border-accentBlue' : ''
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-surfaceAlt">
                <Gem className="h-6 w-6 text-accentBlue2" />
              </span>
              <div>
                <p className="text-lg font-bold text-primaryText">
                  {pack.gems} gems
                </p>
                {pack.bonus && (
                  <p className="text-xs font-medium text-premium">{pack.bonus}</p>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => onPurchase(pack.gems)}
              className="rounded-pill bg-accentBlue px-5 py-2.5 text-sm font-bold text-primaryText transition active:scale-95"
            >
              {pack.price}
            </button>
          </ContentCard>
        ))}
      </div>

      <p className="mt-4 text-center text-xs text-mutedText">
        Demo shop — purchases add gems locally and are not charged.
      </p>
    </div>
  );
}
