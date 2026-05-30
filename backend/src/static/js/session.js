function getAccessToken() {
  return localStorage.getItem("accessToken");
}

function parseJwtPayload(token) {
  if (!token || token.split(".").length < 2) {
    return null;
  }
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded));
  } catch (_error) {
    return null;
  }
}

function getSessionUser() {
  const payload = parseJwtPayload(getAccessToken());
  if (!payload) {
    return null;
  }
  return {
    id: payload.sub || null,
    email: payload.email || null,
    issuedAt: payload.iat || null,
    expiresAt: payload.exp || null,
  };
}

function setSessionUserText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) {
    return;
  }
  const user = getSessionUser();
  if (!user?.id) {
    el.innerHTML = 'Not signed in — <a href="/">Sign in</a>';
    return;
  }
  el.textContent = `Signed in as: ${user.email || user.id}`;
}

function getRefreshToken() {
  return localStorage.getItem("refreshToken");
}

function setSessionTokens(accessToken, refreshToken) {
  if (accessToken) {
    localStorage.setItem("accessToken", accessToken);
  }
  if (refreshToken) {
    localStorage.setItem("refreshToken", refreshToken);
  }
}

function clearSessionTokens() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
}

async function refreshAccessSession() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return false;
  }

  const response = await fetch("/api/v1/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshToken }),
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (_error) {
    return false;
  }

  const data = payload?.data;
  const accessToken = data?.accessToken;
  const nextRefreshToken = data?.refreshToken;
  if (!response.ok || !accessToken || !nextRefreshToken) {
    return false;
  }

  setSessionTokens(accessToken, nextRefreshToken);
  return true;
}

async function sessionFetch(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  if (!headers["Content-Type"] && options.body) {
    headers["Content-Type"] = "application/json";
  }

  const accessToken = getAccessToken();
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(path, { ...options, headers });
  let body = null;
  try {
    body = await response.json();
  } catch (_error) {
    body = null;
  }

  return { status: response.status, ok: response.ok, body };
}

async function sessionProtectedFetch(path, options = {}) {
  let result = await sessionFetch(path, options);
  if (result.status !== 401) {
    return result;
  }

  const renewed = await refreshAccessSession();
  if (!renewed) {
    clearSessionTokens();
    return result;
  }

  result = await sessionFetch(path, options);
  return result;
}

async function revokeAndLogout() {
  const refreshToken = getRefreshToken();
  if (refreshToken) {
    await fetch("/api/v1/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refreshToken }),
    });
  }

  clearSessionTokens();
}
