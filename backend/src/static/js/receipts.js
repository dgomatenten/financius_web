function setReceiptJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    if (id === "receiptsOut" && payload?.ok && Array.isArray(payload?.body?.data?.items)) {
      const items = payload.body.data.items;
      if (items.length === 0) {
        el.innerHTML = "<p class='muted'>No receipts found for this filter.</p>";
        return;
      }
      const headers = ["receiptDate", "totalAmount", "currency", "shopId", "categoryId", "note"];
      const head = headers.map((h) => `<th>${h}</th>`).join("");
      const rows = items
        .map(
          (item) =>
            `<tr>${headers
              .map((h) => `<td>${item[h] ?? item[h.replace(/[A-Z]/g, (m) => `_${m.toLowerCase()}`)] ?? ""}</td>`)
              .join("")}</tr>`
        )
        .join("");
      el.innerHTML = `<div class="table-wrap"><table class="viz-table"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
      return;
    }

    if (payload?.ok && payload?.body?.error == null && id !== "receiptsOut") {
      el.innerHTML = "<p class='status-note'>Completed successfully.</p>";
      return;
    }
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

function setReceiptsSummary(text) {
  const el = document.getElementById("receiptsSummary");
  if (el) {
    el.textContent = text;
  }
}

function buildReceiptQuery() {
  const params = new URLSearchParams();
  const search = document.getElementById("search")?.value?.trim();
  const currency = document.getElementById("currency")?.value?.trim();
  const categoryId = document.getElementById("categoryId")?.value?.trim();

  if (search) params.set("search", search);
  if (currency) params.set("currency", currency);
  if (categoryId) params.set("categoryId", categoryId);

  return params.toString();
}

async function loadReceipts() {
  const query = buildReceiptQuery();
  const path = query ? `/api/v1/receipts?${query}` : "/api/v1/receipts";
  const result = await sessionProtectedFetch(path);
  if (result.status === 401) {
    clearSessionTokens();
    redirectToLogin();
    return;
  }
  setReceiptJson("receiptsOut", result);
  const items = result.body?.data?.items;
  if (Array.isArray(items)) {
    setReceiptsSummary(`Loaded ${items.length} receipts`);
  } else {
    setReceiptsSummary("No receipt data returned");
  }
}

setSessionUserText("sessionUserText");
if (getAccessToken()) {
  loadReceipts();
} else {
  setReceiptsSummary("Not signed in. Please log in to load receipts.");
}

const receiptFilters = document.getElementById("receiptFilters");
if (receiptFilters) {
  receiptFilters.addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadReceipts();
  });
}

const loadReceiptsBtn = document.getElementById("loadReceiptsBtn");
if (loadReceiptsBtn) {
  loadReceiptsBtn.addEventListener("click", loadReceipts);
}

const bulkForm = document.getElementById("bulkForm");
if (bulkForm) {
  bulkForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const operation = document.getElementById("bulkOperation").value;
    const receiptIdsRaw = document.getElementById("bulkReceiptIds").value;
    const categoryId = document.getElementById("bulkCategoryId").value.trim();
    const paymentCardId = document.getElementById("bulkPaymentCardId").value.trim();

    const receiptIds = receiptIdsRaw
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    const result = await sessionProtectedFetch("/api/v1/receipts/bulk", {
      method: "POST",
      body: JSON.stringify({ operation, receiptIds, categoryId, paymentCardId }),
    });
    if (result.status === 401) {
      clearSessionTokens();
      redirectToLogin();
      return;
    }
    setReceiptJson("bulkOut", result);
  });
}

function currentReceiptId() {
  return document.getElementById("receiptIdValue")?.dataset?.receiptId;
}

const loadReceiptDetailBtn = document.getElementById("loadReceiptDetailBtn");
if (loadReceiptDetailBtn) {
  loadReceiptDetailBtn.addEventListener("click", async () => {
    const receiptId = currentReceiptId();
    if (!receiptId) return;

    const result = await sessionProtectedFetch(`/api/v1/receipts/${receiptId}`);
    if (result.status === 401) {
      clearSessionTokens();
      redirectToLogin();
      return;
    }
    setReceiptJson("receiptDetailOut", result);
  });
}

const receiptEditForm = document.getElementById("receiptEditForm");
if (receiptEditForm) {
  receiptEditForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const receiptId = currentReceiptId();
    if (!receiptId) return;

    const payload = {
      categoryId: document.getElementById("editCategoryId").value.trim() || null,
      paymentCardId: document.getElementById("editPaymentCardId").value.trim() || null,
      note: document.getElementById("editNote").value.trim() || null,
    };

    const result = await sessionProtectedFetch(`/api/v1/receipts/${receiptId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    if (result.status === 401) {
      clearSessionTokens();
      redirectToLogin();
      return;
    }
    setReceiptJson("receiptEditOut", result);
  });
}
