/**
 * Dev server: proxy /api → backend local (évite d’appeler Koyeb sans le code à jour).
 * Cible: REACT_APP_DEV_PROXY_TARGET ou http://127.0.0.1:8000
 * Si REACT_APP_API_URL est une URL absolue (ex. Koyeb), axios ne passe pas par ce proxy.
 *
 * proxyTimeout: défaut http-proxy 120s → 504 si Apify/YouTube dépassent; en dev on augmente.
 * REACT_APP_DEV_PROXY_TIMEOUT_MS (ex. 600000 = 10 min).
 */
const { createProxyMiddleware } = require("http-proxy-middleware");

function parseTimeoutMs(raw, fallback) {
  const n = parseInt(String(raw || "").trim(), 10);
  return Number.isFinite(n) && n >= 30000 ? n : fallback;
}

module.exports = function (app) {
  const target =
    process.env.REACT_APP_DEV_PROXY_TARGET ||
    process.env.REACT_APP_API_BACKEND_ORIGIN ||
    "http://127.0.0.1:8000";
  const proxyTimeoutMs = parseTimeoutMs(
    process.env.REACT_APP_DEV_PROXY_TIMEOUT_MS,
    600000
  );

  // eslint-disable-next-line no-console
  console.info(
    `[setupProxy] /api → ${target} (proxyTimeout=${proxyTimeoutMs}ms)`
  );

  app.use(
    "/api",
    createProxyMiddleware({
      target,
      changeOrigin: true,
      proxyTimeout: proxyTimeoutMs,
      timeout: proxyTimeoutMs,
    })
  );
};
