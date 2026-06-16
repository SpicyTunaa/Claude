import {
  FaceSwapError,
  type FaceSwapInput,
  type FaceSwapProvider,
  type FaceSwapResult,
} from './types.js';

interface MagicApiOptions {
  key: string;
  baseUrl: string;
}

/**
 * Adapter for MagicAPI's Face Swap V2 endpoint (https://api.market).
 *
 * The exact request/response shape can vary between API versions, so this
 * adapter is intentionally small and easy to adjust. It sends both images as
 * base64 and expects a JSON body containing the resulting image URL.
 */
export class MagicApiFaceSwapProvider implements FaceSwapProvider {
  readonly name = 'magicapi';

  constructor(private readonly options: MagicApiOptions) {
    if (!options.key) {
      throw new Error('MAGICAPI_KEY is required for the magicapi provider');
    }
  }

  async swap(input: FaceSwapInput): Promise<FaceSwapResult> {
    if (!input.targetImage) {
      throw new FaceSwapError(
        'magicapi provider requires a target/template image',
        400,
      );
    }

    const body = {
      source_image: input.sourceImage.toString('base64'),
      target_image: input.targetImage.toString('base64'),
    };

    let response: Response;
    try {
      response = await fetch(this.options.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-magicapi-key': this.options.key,
          accept: 'application/json',
        },
        body: JSON.stringify(body),
      });
    } catch (err) {
      throw new FaceSwapError(`Failed to reach MagicAPI: ${String(err)}`);
    }

    if (!response.ok) {
      const text = await safeText(response);
      throw new FaceSwapError(
        `MagicAPI returned ${response.status}: ${text}`,
        response.status >= 500 ? 502 : response.status,
      );
    }

    const data = (await response.json()) as Record<string, unknown>;
    const imageUrl =
      pickString(data, 'image_url') ??
      pickString(data, 'output') ??
      pickString(data, 'result');

    if (!imageUrl) {
      throw new FaceSwapError('MagicAPI response did not contain an image URL');
    }

    return { imageUrl, provider: this.name };
  }
}

function pickString(obj: Record<string, unknown>, key: string): string | undefined {
  const value = obj[key];
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

async function safeText(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return '<unreadable body>';
  }
}
