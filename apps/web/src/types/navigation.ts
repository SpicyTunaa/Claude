export type ScreenId = 'gallery' | 'create' | 'settings' | 'shop';

export interface GalleryItem {
  id: string;
  /** The user's source selfie, shown as the "YOUR SELFIE" preview. */
  sourceUrl: string;
  /** The generated/face-swapped result image. */
  resultUrl: string;
  prompt?: string;
  createdAt: number;
}
