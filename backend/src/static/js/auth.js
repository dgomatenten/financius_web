function setJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

async function loginWithGoogleIdToken(idToken) {
  const result = await sessionFetch("/api/v1/auth/google", {
    method: "POST",
    body: JSON.stringify({ idToken }),
  });
  const accessToken = result.body?.data?.accessToken;
  const refreshToken = result.body?.data?.refreshToken;
  setSessionTokens(accessToken, refreshToken);
  setJson("googleOut", result);
  if (accessToken) {
    window.location.href = getPostLoginRedirectTarget();
  }
}

const googleClientId = window.FINANCIUS_GOOGLE_CLIENT_ID;
const googleRedirectUri = window.FINANCIUS_GOOGLE_REDIRECT_URI || `${window.location.origin}/login`;
const googleSignInHint = document.getElementById("googleSignInHint");
const googleSignInStart = document.getElementById("googleSignInStart");
const GOOGLE_OAUTH_STATE_KEY = "financius_google_oauth_state";

function randomState() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function buildGoogleOauthUrl(clientId, state) {
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: googleRedirectUri,
    response_type: "id_token",
    scope: "openid email profile",
    prompt: "select_account",
    state,
    nonce: state,
  });
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
}

async function maybeHandleGoogleOauthRedirect() {
  const hash = new URLSearchParams(window.location.hash.slice(1));
  const idToken = hash.get("id_token");
  if (!idToken) {
    return;
  }

  const returnedState = hash.get("state");
  const expectedState = sessionStorage.getItem(GOOGLE_OAUTH_STATE_KEY);
  sessionStorage.removeItem(GOOGLE_OAUTH_STATE_KEY);

  history.replaceState({}, document.title, window.location.pathname);

  if (!returnedState || !expectedState || returnedState !== expectedState) {
    if (googleSignInHint) {
      googleSignInHint.textContent = "Google login failed state check. Please try again.";
    }
    return;
  }

  await loginWithGoogleIdToken(idToken);
}

if (googleClientId && googleClientId !== "replace-me") {
  if (googleSignInHint) {
    googleSignInHint.textContent = "Continue with Google to sign in.";
  }
  if (googleSignInStart) {
    googleSignInStart.addEventListener("click", () => {
      const state = randomState();
      sessionStorage.setItem(GOOGLE_OAUTH_STATE_KEY, state);
      window.location.assign(buildGoogleOauthUrl(googleClientId, state));
    });
  }
} else if (googleSignInHint) {
  googleSignInHint.textContent = "Google Sign-In is not configured on this environment.";
  if (googleSignInStart) {
    googleSignInStart.disabled = true;
  }
}

maybeHandleGoogleOauthRedirect();

const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    const result = await sessionFetch("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    const accessToken = result.body?.data?.accessToken;
    const refreshToken = result.body?.data?.refreshToken;
    setSessionTokens(accessToken, refreshToken);
    setJson("loginOut", result);
    if (accessToken) {
      window.location.href = getPostLoginRedirectTarget();
    }
  });
}

const registerForm = document.getElementById("registerForm");
if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("registerEmail").value;
    const password = document.getElementById("registerPassword").value;
    const result = await sessionFetch("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    const accessToken = result.body?.data?.accessToken;
    const refreshToken = result.body?.data?.refreshToken;
    setSessionTokens(accessToken, refreshToken);
    setJson("registerOut", result);
    if (accessToken) {
      window.location.href = getPostLoginRedirectTarget();
    }
  });
}

const googleLoginForm = document.getElementById("googleLoginForm");
if (googleLoginForm) {
  googleLoginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const idToken = document.getElementById("googleIdToken").value.trim();
    await loginWithGoogleIdToken(idToken);
  });
}
