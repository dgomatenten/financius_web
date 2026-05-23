function setSyncJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

const syncStatusBtn = document.getElementById("syncStatusBtn");
if (syncStatusBtn) {
  syncStatusBtn.addEventListener("click", async () => {
    const result = await sessionProtectedFetch("/api/v1/sync/status");
    if (result.status === 401) {
      clearSessionTokens();
      window.location.href = "/login";
      return;
    }
    setSyncJson("syncStatusOut", result);
  });
}

const sampleSyncBtn = document.getElementById("sampleSyncBtn");
if (sampleSyncBtn) {
  sampleSyncBtn.addEventListener("click", async () => {
    const nowIso = new Date().toISOString();
    const payload = {
      deviceId: "web-sample-device",
      receipts: [
        {
          externalId: `sample-receipt-${Date.now()}`,
          receiptDate: nowIso,
          currency: "USD",
          totalAmount: 17.25,
          lineItems: [
            { name: "Coffee", quantity: 1, unitPrice: 4.25 },
            { name: "Sandwich", quantity: 1, unitPrice: 13.0 },
          ],
        },
      ],
      categories: [{ externalId: "cat-food", name: "Food" }],
      shops: [{ externalId: "shop-central", name: "Central Cafe" }],
      cards: [{ externalId: "card-main", nickname: "Main Visa", cardType: "credit" }],
    };

    const result = await sessionProtectedFetch("/api/v1/sync", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (result.status === 401) {
      clearSessionTokens();
      window.location.href = "/login";
      return;
    }
    setSyncJson("sampleSyncOut", result);
  });
}
