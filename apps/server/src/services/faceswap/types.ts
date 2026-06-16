export interface FaceSwapInput {
  /** The image that provides the face to insert (the user's selfie). */
  sourceImage: Buffer;
  sourceMimeType: string;
  /**
   * Optional target/template image to swap the face onto. When omitted, a
   * provider that supports text-to-image generation can use `prompt` instead.
   */
  targetImage?: Buffer;
  targetMimeType?: string;
  /** Free-form description, used by generative providers. */
  prompt?: string;
}

export interface FaceSwapResult {
  /** Resulting image as a data URL (data:image/...;base64,...) or remote URL. */
  imageUrl: string;
  provider: string;
}

export interface FaceSwapProvider {
  readonly name: string;
  swap(input: FaceSwapInput): Promise<FaceSwapResult>;
}

export class FaceSwapError extends Error {
  constructor(
    message: string,
    readonly statusCode = 502,
  ) {
    super(message);
    this.name = 'FaceSwapError';
  }
}
