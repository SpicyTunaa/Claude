import crypto from 'crypto';

export interface TelegramUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
  is_premium?: boolean;
}

export interface ParsedInitData {
  user?: TelegramUser;
  authDate: number;
  queryId?: string;
  raw: URLSearchParams;
}

export interface ValidationOptions {
  botToken: string;
  /** Reject data older than this many seconds. 0 disables the check. */
  maxAgeSeconds?: number;
}

export type ValidationResult =
  | { ok: true; data: ParsedInitData }
  | { ok: false; reason: string };

/**
 * Validates the `initData` string passed by the Telegram Mini App client.
 *
 * The algorithm follows Telegram's spec:
 *   secret_key = HMAC_SHA256(bot_token, "WebAppData")
 *   hash       = HMAC_SHA256(data_check_string, secret_key)
 *
 * See https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
 */
export function validateInitData(
  initData: string,
  { botToken, maxAgeSeconds = 0 }: ValidationOptions,
): ValidationResult {
  if (!initData) {
    return { ok: false, reason: 'empty_init_data' };
  }

  const params = new URLSearchParams(initData);
  const hash = params.get('hash');
  if (!hash) {
    return { ok: false, reason: 'missing_hash' };
  }

  // Build the data-check-string from every field except `hash`, sorted by key.
  const pairs: string[] = [];
  for (const [key, value] of params.entries()) {
    if (key === 'hash') continue;
    pairs.push(`${key}=${value}`);
  }
  pairs.sort();
  const dataCheckString = pairs.join('\n');

  const secretKey = crypto
    .createHmac('sha256', 'WebAppData')
    .update(botToken)
    .digest();
  const computedHash = crypto
    .createHmac('sha256', secretKey)
    .update(dataCheckString)
    .digest('hex');

  // Constant-time comparison to avoid timing attacks.
  const expected = Buffer.from(computedHash, 'hex');
  const actual = Buffer.from(hash, 'hex');
  if (
    expected.length !== actual.length ||
    !crypto.timingSafeEqual(expected, actual)
  ) {
    return { ok: false, reason: 'bad_signature' };
  }

  const authDate = Number(params.get('auth_date') ?? 0);
  if (maxAgeSeconds > 0) {
    const ageSeconds = Math.floor(Date.now() / 1000) - authDate;
    if (ageSeconds > maxAgeSeconds) {
      return { ok: false, reason: 'expired' };
    }
  }

  let user: TelegramUser | undefined;
  const userRaw = params.get('user');
  if (userRaw) {
    try {
      user = JSON.parse(userRaw) as TelegramUser;
    } catch {
      return { ok: false, reason: 'malformed_user' };
    }
  }

  return {
    ok: true,
    data: {
      user,
      authDate,
      queryId: params.get('query_id') ?? undefined,
      raw: params,
    },
  };
}
