#!/usr/bin/env node

/*
Browser-assisted Panasonic Comfort Cloud OAuth bootstrap.

Usage:
  cd /tmp/pwprobe && node /Users/Liam/Developer/GitHub/panasonic_cc/tools/panasonic_oauth_helper.mjs
  cd /tmp/pwprobe && node /Users/Liam/Developer/GitHub/panasonic_cc/tools/panasonic_oauth_helper.mjs /tmp/panasonic-refresh-token.json

Prerequisites:
  - playwright installed in the current Node environment
  - Chromium installed via: npx playwright install chromium

The script opens Panasonic's hosted login page in a real browser, waits for you
to finish the login manually, captures the OAuth authorization code from the
redirect response, exchanges it for tokens, and optionally writes the refresh
token payload to disk.
*/

const crypto = require("node:crypto");
const fs = require("node:fs/promises");
const process = require("node:process");
const readline = require("node:readline/promises");
const { chromium } = require("playwright");

const APP_CLIENT_ID = "Xmy6xIYIitMxngjB2rHvlm6HSDNnaMJx";
const AUTH0_CLIENT = "eyJuYW1lIjoiYXV0aDAuanMtdWxwIiwidmVyc2lvbiI6IjkuMjMuMiJ9";
const REDIRECT_URI =
  "panasonic-iot-cfc://authglb.digital.panasonic.com/android/com.panasonic.ACCsmart/callback";
const BASE_PATH_AUTH = "https://authglb.digital.panasonic.com";
const PANASONIC_OAUTH_SCOPE =
  "openid offline_access comfortcloud.control a2w.control";

function randomString(length) {
  return crypto
    .randomBytes(length * 2)
    .toString("base64url")
    .replace(/[^A-Za-z0-9]/g, "")
    .slice(0, length);
}

function buildAuthorizeUrl(codeChallenge, state, nonce) {
  const params = new URLSearchParams({
    scope: PANASONIC_OAUTH_SCOPE,
    audience: `https://digital.panasonic.com/${APP_CLIENT_ID}/api/v1/`,
    protocol: "oauth2",
    response_type: "code",
    code_challenge: codeChallenge,
    code_challenge_method: "S256",
    auth0Client: AUTH0_CLIENT,
    client_id: APP_CLIENT_ID,
    redirect_uri: `${REDIRECT_URI}?lang=en`,
    state,
    nonce,
  });
  return `${BASE_PATH_AUTH}/authorize?${params.toString()}`;
}

function extractCode(locationHeader) {
  if (!locationHeader) {
    return null;
  }
  try {
    const parsed = new URL(locationHeader);
    return parsed.searchParams.get("code");
  } catch {
    return null;
  }
}

async function exchangeCodeForToken(code, codeVerifier) {
  const response = await fetch(`${BASE_PATH_AUTH}/oauth/token`, {
    method: "POST",
    headers: {
      "Auth0-Client": AUTH0_CLIENT,
      "Content-Type": "application/json",
      "User-Agent": "okhttp/4.10.0",
    },
    body: JSON.stringify({
      scope: "openid",
      client_id: APP_CLIENT_ID,
      grant_type: "authorization_code",
      code,
      redirect_uri: REDIRECT_URI,
      code_verifier: codeVerifier,
    }),
  });

  const text = await response.text();
  if (!response.ok) {
    throw new Error(`oauth/token failed (${response.status}): ${text}`);
  }
  return JSON.parse(text);
}

async function main() {
  const outputPath = process.argv[2];
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const codeVerifier = randomString(43);
  const codeChallenge = crypto
    .createHash("sha256")
    .update(codeVerifier)
    .digest("base64url");
  const state = randomString(20);
  const nonce = randomString(20);
  const authorizeUrl = buildAuthorizeUrl(codeChallenge, state, nonce);

  let authCode;
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on("response", async (response) => {
    const location = response.headers().location;
    if (!location?.startsWith("panasonic-iot-cfc://")) {
      return;
    }
    const code = extractCode(location);
    if (code) {
      authCode = code;
    }
  });

  console.log("Opening Panasonic login page in Chromium.");
  console.log("Complete the login manually in the browser window.");
  console.log("This script will capture the OAuth code from the final redirect.");

  await page.goto(authorizeUrl, { waitUntil: "domcontentloaded" });

  while (!authCode) {
    const answer = await rl.question(
      "Press Enter after you complete login in the browser, or type 'cancel' to abort: ",
    );
    if (answer.trim().toLowerCase() === "cancel") {
      throw new Error("Cancelled.");
    }
    await page.waitForTimeout(1000);
  }

  const tokenResponse = await exchangeCodeForToken(authCode, codeVerifier);
  const tokenPayload = {
    refresh_token: tokenResponse.refresh_token,
    scope: tokenResponse.scope,
    access_token: tokenResponse.access_token,
    expires_in: tokenResponse.expires_in,
    id_token: tokenResponse.id_token,
  };

  console.log("\nRefresh token captured successfully.\n");
  console.log(JSON.stringify(tokenPayload, null, 2));

  if (outputPath) {
    await fs.writeFile(outputPath, JSON.stringify(tokenPayload, null, 2));
    console.log(`\nSaved token payload to ${outputPath}`);
  }

  await browser.close();
  rl.close();
}

main().catch(async (error) => {
  console.error(`\nError: ${error.message}`);
  process.exitCode = 1;
});
