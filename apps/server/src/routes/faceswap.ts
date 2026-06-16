import { Router } from 'express';
import multer from 'multer';
import { requireTelegramAuth } from '../middleware/auth.js';
import { getFaceSwapProvider, FaceSwapError } from '../services/faceswap/index.js';

const ALLOWED_MIME = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10 MB

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: MAX_FILE_BYTES, files: 2 },
});

export const faceSwapRouter = Router();

faceSwapRouter.post(
  '/',
  requireTelegramAuth,
  upload.fields([
    { name: 'source', maxCount: 1 },
    { name: 'target', maxCount: 1 },
  ]),
  async (req, res) => {
    const files = req.files as
      | Record<string, Express.Multer.File[]>
      | undefined;
    const source = files?.source?.[0];
    const target = files?.target?.[0];
    const prompt =
      typeof req.body?.prompt === 'string' ? req.body.prompt : undefined;

    if (!source) {
      res.status(400).json({ error: 'source_image_required' });
      return;
    }
    if (!ALLOWED_MIME.has(source.mimetype)) {
      res.status(415).json({ error: 'unsupported_source_type' });
      return;
    }
    if (target && !ALLOWED_MIME.has(target.mimetype)) {
      res.status(415).json({ error: 'unsupported_target_type' });
      return;
    }

    try {
      const provider = getFaceSwapProvider();
      const result = await provider.swap({
        sourceImage: source.buffer,
        sourceMimeType: source.mimetype,
        targetImage: target?.buffer,
        targetMimeType: target?.mimetype,
        prompt,
      });
      res.json(result);
    } catch (err) {
      if (err instanceof FaceSwapError) {
        res.status(err.statusCode).json({ error: 'face_swap_failed', message: err.message });
        return;
      }
      console.error('Unexpected face swap error:', err);
      res.status(500).json({ error: 'internal_error' });
    }
  },
);
