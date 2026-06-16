import { getWebApp } from './telegram';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:4000';

export interface FaceSwapResponse {
  imageUrl: string;
  provider: string;
}

export interface FaceSwapRequest {
  source: File;
  target?: File;
  prompt?: string;
}

/**
 * Sends the face-swap request to the backend, attaching the Telegram initData
 * as a Bearer-style `tma` token so the server can authenticate the user.
 */
export async function requestFaceSwap(
  req: FaceSwapRequest,
): Promise<FaceSwapResponse> {
  const form = new FormData();
  form.append('source', req.source);
  if (req.target) form.append('target', req.target);
  if (req.prompt) form.append('prompt', req.prompt);

  const initData = getWebApp()?.initData ?? '';

  const response = await fetch(`${API_BASE_URL}/api/faceswap`, {
    method: 'POST',
    headers: {
      Authorization: `tma ${initData}`,
    },
    body: form,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(
      detail.message || detail.error || `Request failed (${response.status})`,
    );
  }

  return (await response.json()) as FaceSwapResponse;
}
