import type { FaceSwapInput, FaceSwapProvider, FaceSwapResult } from './types.js';

/**
 * A no-network provider used for local development and tests. It simply echoes
 * the source image back as a data URL so the full request/response flow can be
 * exercised without any external API keys.
 */
export class MockFaceSwapProvider implements FaceSwapProvider {
  readonly name = 'mock';

  async swap(input: FaceSwapInput): Promise<FaceSwapResult> {
    // Simulate processing latency.
    await new Promise((resolve) => setTimeout(resolve, 600));
    const base64 = input.sourceImage.toString('base64');
    return {
      imageUrl: `data:${input.sourceMimeType};base64,${base64}`,
      provider: this.name,
    };
  }
}
