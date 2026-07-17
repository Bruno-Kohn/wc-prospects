// Cloudflare Worker - SofaScore Proxy
// Deploy em: https://dash.cloudflare.com/ → Workers & Pages → Create
// Nome sugerido: sofascore-proxy

const SOFASCORE_BASE = "https://www.sofascore.com/api/v1";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default {
  async fetch(request) {
    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // Only allow specific endpoints
    const allowedPatterns = [
      /^\/search\/all$/,
      /^\/player\/\d+$/,
      /^\/player\/\d+\/image$/,
    ];

    if (!allowedPatterns.some((p) => p.test(path))) {
      return new Response(JSON.stringify({ error: "Endpoint not allowed" }), {
        status: 403,
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    // Forward request to SofaScore
    const sofascoreUrl = `${SOFASCORE_BASE}${path}${url.search}`;
    const resp = await fetch(sofascoreUrl, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        Accept: "application/json",
        "Accept-Language": "en-US,en;q=0.9",
      },
    });

    const body = await resp.text();
    return new Response(body, {
      status: resp.status,
      headers: {
        ...CORS_HEADERS,
        "Content-Type": resp.headers.get("Content-Type") || "application/json",
      },
    });
  },
};
