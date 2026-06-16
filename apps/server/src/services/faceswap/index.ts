import { config } from '../../config.js';
import { MagicApiFaceSwapProvider } from './magicApiProvider.js';
import { MockFaceSwapProvider } from './mockProvider.js';
import type { FaceSwapProvider } from './types.js';

let cached: FaceSwapProvider | null = null;

/**
 * Returns the configured face-swap provider, instantiating it lazily so that
 * missing credentials only fail when the provider is actually selected.
 */
export function getFaceSwapProvider(): FaceSwapProvider {
  if (cached) return cached;

  switch (config.faceSwap.provider) {
    case 'magicapi':
      cached = new MagicApiFaceSwapProvider(config.faceSwap.magicapi);
      break;
    case 'mock':
    case '':
      cached = new MockFaceSwapProvider();
      break;
    default:
      throw new Error(
        `Unknown FACE_SWAP_PROVIDER: "${config.faceSwap.provider}". ` +
          `Supported values: magicapi, mock.`,
      );
  }

  return cached;
}

export * from './types.js';
