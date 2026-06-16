# LumiPic Clone — Telegram Mini App for AI Face Swap

A LumiPic-style [Telegram Mini App](https://core.telegram.org/bots/webapps) that
lets users upload a selfie, optionally add a template image and a text prompt,
and receive an AI face-swapped image — all without leaving Telegram.

This repo is a working scaffold built from the architecture described in the
project guide: a **Next.js** front end rendered inside Telegram's WebView and an
**Express** back end that validates Telegram `initData` and talks to a pluggable
AI face-swap provider.

## Architecture

```
┌──────────────────────────┐        ┌───────────────────────────┐
│  apps/web (Next.js)       │        │  apps/server (Express)     │
│  - Telegram WebApp SDK    │  HTTPS │  - initData validation     │
│  - Theme-aware UI         ├───────►│  - /api/faceswap endpoint  │
│  - Image upload + prompt  │  multipart  - provider abstraction  │
└──────────────────────────┘        └─────────────┬─────────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │  Face swap API   │
                                          │  (MagicAPI / …)  │
                                          └──────────────────┘
```

| Path          | Stack                                   | Responsibility                          |
| ------------- | --------------------------------------- | --------------------------------------- |
| `apps/web`    | Next.js 14 (App Router), TS, Tailwind   | Mini App UI, Telegram SDK integration   |
| `apps/server` | Express, TS, Multer, Zod                | Auth, file handling, AI provider calls  |

## Prerequisites

- Node.js >= 18.18
- A Telegram bot created via [@BotFather](https://t.me/botfather) (for `BOT_TOKEN`)
- (Optional) An API key for a face-swap provider; the default `mock` provider
  needs none.

## Getting started

First clone the repo and `cd` into it — all commands below must run from the
project root, **not** your home directory:

```bash
git clone https://github.com/SpicyTunaa/Claude.git
cd Claude
git checkout claude/telegram-mini-app-faceswap-ayxbec
```

### macOS / Linux

```bash
# 1. Install all workspaces
npm install

# 2. Configure the backend (then edit the file to set BOT_TOKEN)
cp apps/server/.env.example apps/server/.env

# 3. Configure the frontend
cp apps/web/.env.example apps/web/.env.local

# 4. Run both apps (web on :3000, server on :4000)
npm run dev
```

### Windows (cmd)

`cp` does not exist in `cmd`; use `copy` instead:

```cmd
npm install
copy apps\server\.env.example apps\server\.env
copy apps\web\.env.example apps\web\.env.local
npm run dev
```

In **PowerShell**, use `Copy-Item apps\server\.env.example apps\server\.env`.

After copying, open `apps/server/.env` and set `BOT_TOKEN`. Leave
`FACE_SWAP_PROVIDER=mock` for now.

### Local development without Telegram

When you open `http://localhost:3000` directly in a browser there is no
`initData`, so the server will reject the request. To exercise the full flow
locally, set `ALLOW_INSECURE_AUTH=true` in `apps/server/.env`. **Never enable
this in production** — it disables user authentication.

## Connecting it to Telegram

1. In [@BotFather](https://t.me/botfather): `/newbot` → copy the token into
   `BOT_TOKEN`.
2. `/newapp` → select your bot, set a title/description, and provide the public
   HTTPS URL of the deployed front end.
3. Telegram only loads Mini Apps over HTTPS. For local testing, expose the dev
   server with a tunnel (e.g. `ngrok http 3000`) and use that URL in BotFather.

## How authentication works

The Mini App sends Telegram's signed `initData` to the backend in the
`Authorization: tma <initData>` header. The server recomputes the HMAC-SHA256
signature using `BOT_TOKEN` and rejects any request whose signature does not
match or whose `auth_date` is older than `INITDATA_MAX_AGE_SECONDS`. See
`apps/server/src/telegram/initData.ts`.

## Swapping in a real face-swap provider

Providers implement the `FaceSwapProvider` interface in
`apps/server/src/services/faceswap/types.ts`. Two implementations ship:

- **`mock`** — echoes the source image back; no network/keys required.
- **`magicapi`** — adapter for MagicAPI's Face Swap V2 API.

To use MagicAPI, set in `apps/server/.env`:

```
FACE_SWAP_PROVIDER=magicapi
MAGICAPI_KEY=your_key_here
```

Add another provider by creating a class that implements `FaceSwapProvider` and
registering it in `apps/server/src/services/faceswap/index.ts`.

## Deployment

- **Front end** → Vercel/Netlify. Set `NEXT_PUBLIC_API_BASE_URL` to the public
  backend URL.
- **Back end** → any Node host (VPS, Render, Fly.io, a container). Set
  `BOT_TOKEN`, `CORS_ORIGINS` (your Mini App origin), and the provider keys.

## Scripts

| Command              | Description                          |
| -------------------- | ------------------------------------ |
| `npm run dev`        | Run web + server together            |
| `npm run build`      | Build both apps                      |
| `npm run lint`       | Lint the web app                     |

## Security notes

- `initData` is validated on every request; do not trust `initDataUnsafe`.
- Uploads are capped at 10 MB and restricted to JPEG/PNG/WebP.
- Keep all API keys server-side; the front end never sees provider credentials.
