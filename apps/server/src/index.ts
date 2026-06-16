import cors from 'cors';
import express from 'express';
import { config } from './config.js';
import { faceSwapRouter } from './routes/faceswap.js';

const app = express();

app.use(
  cors({
    origin: config.corsOrigins.length > 0 ? config.corsOrigins : true,
  }),
);
app.use(express.json({ limit: '1mb' }));

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', provider: config.faceSwap.provider });
});

app.use('/api/faceswap', faceSwapRouter);

app.listen(config.port, () => {
  console.log(`LumiPic server listening on http://localhost:${config.port}`);
  console.log(`Face swap provider: ${config.faceSwap.provider}`);
  if (config.allowInsecureAuth) {
    console.warn(
      'WARNING: ALLOW_INSECURE_AUTH is enabled. Disable this in production.',
    );
  }
});
