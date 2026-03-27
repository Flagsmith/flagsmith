import { createServer } from "node:http";
import { randomBytes, createHash } from "node:crypto";

const CLIENT_ID = "ZLsLu3hhJI4GlhNsGeFVC3K2U3QBGfXtmc0EcyiG";
const REDIRECT_URI = "http://localhost:3000/oauth/callback";
const API_URL = "http://localhost:8000";
const PORT = 3000;

// Generate PKCE values
const codeVerifier = randomBytes(96).toString("base64url").slice(0, 128);
const codeChallenge = createHash("sha256")
  .update(codeVerifier)
  .digest("base64url");

const authorizeUrl =
  `${API_URL}/o/authorize/?` +
  new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    scope: "mcp",
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
  });

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  if (url.pathname === "/oauth/callback") {
    const code = url.searchParams.get("code");
    const error = url.searchParams.get("error");

    if (error) {
      res.writeHead(400, { "Content-Type": "text/plain" });
      res.end(`Error: ${error}\n${url.searchParams.get("error_description")}`);
      return;
    }

    if (!code) {
      res.writeHead(400, { "Content-Type": "text/plain" });
      res.end("No authorization code received");
      return;
    }

    console.log(`\nReceived authorization code: ${code}`);
    console.log("Exchanging for token...\n");

    // Exchange code for token
    const tokenRes = await fetch(`${API_URL}/o/token/`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        code,
        redirect_uri: REDIRECT_URI,
        client_id: CLIENT_ID,
        code_verifier: codeVerifier,
      }),
    });

    const tokenData = await tokenRes.json();
    console.log("Token response:", JSON.stringify(tokenData, null, 2));

    res.writeHead(200, { "Content-Type": "text/html" });
    res.end(`<pre>${JSON.stringify(tokenData, null, 2)}</pre>`);

    // Done - shut down
    setTimeout(() => {
      console.log("\nDone. Shutting down.");
      process.exit(0);
    }, 1000);
  } else {
    res.writeHead(302, { Location: authorizeUrl });
    res.end();
  }
});

server.listen(PORT, () => {
  console.log(`OAuth test server running on http://localhost:${PORT}`);
  console.log(`\nOpen http://localhost:${PORT} in your browser to start the flow.\n`);
});
