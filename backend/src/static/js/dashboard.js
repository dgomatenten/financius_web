function setJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    const bodyData = payload?.body?.data;
    if (bodyData && typeof bodyData === "object") {
      const rows = Object.entries(bodyData)
        .map(([key, value]) => `<div class="row-split"><strong>${key}</strong><span>${typeof value === "object" ? JSON.stringify(value) : String(value)}</span></div>`)
        .join("");
      el.innerHTML = `<div class="list-clean">${rows}</div>`;
      return;
    }
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

setSessionUserText("sessionUserText");

const healthBtn = document.getElementById("healthBtn");
if (healthBtn) {
  healthBtn.addEventListener("click", async () => {
    const result = await sessionFetch("/api/v1/health");
    setJson("healthOut", result);
  });
}

const syncBtn = document.getElementById("syncBtn");
if (syncBtn) {
  syncBtn.addEventListener("click", async () => {
    const result = await sessionProtectedFetch("/api/v1/sync/status");
    if (result.status === 401) {
      redirectToLogin();
      return;
    }
    setJson("syncOut", result);
  });
}

const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    await revokeAndLogout();
    window.location.href = "/login";
  });
}
