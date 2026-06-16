import type { NextFunction, Request, Response } from 'express';
import { config } from '../config.js';
import { validateInitData, type TelegramUser } from '../telegram/initData.js';

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      telegramUser?: TelegramUser;
    }
  }
}

/**
 * Express middleware that verifies the Telegram `initData` sent by the Mini App.
 *
 * The client must send the raw initData string in the `Authorization` header as
 * `tma <initData>` (or in the `X-Telegram-Init-Data` header).
 */
export function requireTelegramAuth(
  req: Request,
  res: Response,
  next: NextFunction,
): void {
  const initData = extractInitData(req);

  if (!initData) {
    if (config.allowInsecureAuth) {
      next();
      return;
    }
    res.status(401).json({ error: 'missing_init_data' });
    return;
  }

  const result = validateInitData(initData, {
    botToken: config.botToken,
    maxAgeSeconds: config.initDataMaxAgeSeconds,
  });

  if (!result.ok) {
    res.status(401).json({ error: 'invalid_init_data', reason: result.reason });
    return;
  }

  req.telegramUser = result.data.user;
  next();
}

function extractInitData(req: Request): string | null {
  const header = req.header('authorization');
  if (header && header.toLowerCase().startsWith('tma ')) {
    return header.slice(4).trim();
  }
  const custom = req.header('x-telegram-init-data');
  if (custom) {
    return custom.trim();
  }
  return null;
}
