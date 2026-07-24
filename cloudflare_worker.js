/**
 * Cloudflare Worker - Proxy para API do SofaScore
 * 
 * Deploy:
 * 1. Vá em https://dash.cloudflare.com → Workers & Pages → Create
 * 2. Clique "Create Worker"
 * 3. Cole este código e faça Deploy
 * 4. Copie a URL do worker (ex: https://sofascore-proxy.seu-user.workers.dev)
 * 5. Adicione no Streamlit Cloud secrets: SOFASCORE_PROXY_URL = "https://sofascore-proxy.seu-user.workers.dev"
 */

export default {
  async fetch(request) {
    const url = new URL(request.url);
    
    // Remover o path prefix se houver
    const targetPath = url.pathname;
    const targetSearch = url.search;
    
    // Montar URL do SofaScore
    const sofascoreUrl = `https://www.sofascore.com/api/v1${targetPath}${targetSearch}`;
    
    const headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
      "Referer": "https://www.sofascore.com/",
      "Origin": "https://www.sofascore.com",
      "Cache-Control": "no-cache",
    };

    const response = await fetch(sofascoreUrl, { headers });
    
    // Retornar com CORS headers
    const newHeaders = new Headers(response.headers);
    newHeaders.set("Access-Control-Allow-Origin", "*");
    newHeaders.set("Access-Control-Allow-Methods", "GET, OPTIONS");
    
    return new Response(response.body, {
      status: response.status,
      headers: newHeaders,
    });
  },
};
