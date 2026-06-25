function setPairingJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

const pairingPayloadBtn = document.getElementById("pairingPayloadBtn");
if (pairingPayloadBtn) {
  pairingPayloadBtn.addEventListener("click", async () => {
    const result = await sessionProtectedFetch("/api/v1/pairing/qr");
    if (result.status === 401) {
      clearSessionTokens();
      redirectToLogin();
      return;
    }
    setPairingJson("pairingPayloadOut", result);
  });
}
