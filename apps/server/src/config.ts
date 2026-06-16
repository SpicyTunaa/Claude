import dotenv from 'dotenv';

dotenv.config();

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optional(name: string, fallback = ''): string {
  return process.env[name] ?? fallback;
}

export const config = {
  port: Number(process.env.PORT ?? 4000),
  botToken: required('BOT_TOKEN'),
  corsOrigins: optional('CORS_ORIGINS', 'http://localhost:3000')
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean),
  initDataMaxAgeSeconds: Number(process.env.INITDATA_MAX_AGE_SECONDS ?? 86400),
  allowInsecureAuth: optional('ALLOW_INSECURE_AUTH', 'false') === 'true',
  faceSwap: {
    provider: optional('FACE_SWAP_PROVIDER', 'mock'),
    magicapi: {
      key: optional('MAGICAPI_KEY'),
      baseUrl: optional(
        'MAGICAPI_BASE_URL',
        'https://api.magicapi.dev/api/v1/magicapi/faceswap',
      ),
    },
  },
} as const;

export type AppConfig = typeof config;
