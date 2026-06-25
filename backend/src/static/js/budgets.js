function setBudgetJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    if (payload?.ok && payload?.body?.data) {
      const data = payload.body.data;
      const items = Array.isArray(data.items) ? data.items : [];
      if (items.length > 0) {
        const headers = Object.keys(items[0]);
        const head = headers.map((h) => `<th>${h}</th>`).join("");
        const rows = items
          .map((item) => `<tr>${headers.map((h) => `<td>${item[h] ?? ""}</td>`).join("")}</tr>`)
          .join("");
        el.innerHTML = `<div class="table-wrap"><table class="viz-table"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
        return;
      }
      if (Array.isArray(data.categories)) {
        const rows = data.categories
          .map(
            (c) =>
              `<tr><td>${c.categoryName || c.categoryId || "-"}</td><td>${c.budget ?? 0}</td><td>${c.spent ?? 0}</td><td>${c.remaining ?? 0}</td><td>${c.progressPct ?? 0}%</td></tr>`
          )
          .join("");
        el.innerHTML = `<div class="table-wrap"><table class="viz-table"><thead><tr><th>Category</th><th>Budget</th><th>Spent</th><th>Remaining</th><th>Progress</th></tr></thead><tbody>${rows}</tbody></table></div>`;
        return;
      }
    }
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

function currentMonth() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

function readBudgetMonth() {
  return (
    document.getElementById("budgetMonth")?.value?.trim() ||
    document.getElementById("progressMonth")?.value?.trim() ||
    currentMonth()
  );
}

async function loadBudgets() {
  const month = readBudgetMonth();
  const result = await sessionProtectedFetch(`/api/v1/budgets?month=${encodeURIComponent(month)}`);
  if (result.status === 401) {
    clearSessionTokens();
    redirectToLogin();
    return;
  }
  setBudgetJson("budgetsOut", result);
}

async function loadBudgetProgress() {
  const month = readBudgetMonth();
  const result = await sessionProtectedFetch(`/api/v1/budgets/progress?month=${encodeURIComponent(month)}`);
  if (result.status === 401) {
    clearSessionTokens();
    redirectToLogin();
    return;
  }
  setBudgetJson("budgetProgressOut", result);
}

const loadBudgetsBtn = document.getElementById("loadBudgetsBtn");
if (loadBudgetsBtn) {
  loadBudgetsBtn.addEventListener("click", loadBudgets);
}

const loadBudgetProgressBtn = document.getElementById("loadBudgetProgressBtn");
if (loadBudgetProgressBtn) {
  loadBudgetProgressBtn.addEventListener("click", loadBudgetProgress);
}

const budgetForm = document.getElementById("budgetForm");
if (budgetForm) {
  budgetForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      month: document.getElementById("budgetMonth").value.trim(),
      categoryId: document.getElementById("budgetCategoryId").value.trim() || null,
      mode: document.getElementById("budgetMode").value,
      amount: Number(document.getElementById("budgetAmount").value || 0),
      rolloverEnabled: document.getElementById("budgetRollover").checked,
    };

    const adjustmentRaw = document.getElementById("budgetAdjustmentPct").value.trim();
    if (adjustmentRaw) {
      payload.adjustmentPct = Number(adjustmentRaw);
    }

    const result = await sessionProtectedFetch("/api/v1/budgets", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (result.status === 401) {
      clearSessionTokens();
      redirectToLogin();
      return;
    }

    setBudgetJson("budgetsOut", result);
    await loadBudgets();
  });
}

const budgetMonthInput = document.getElementById("budgetMonth");
if (budgetMonthInput && !budgetMonthInput.value) {
  budgetMonthInput.value = currentMonth();
}

const progressMonthInput = document.getElementById("progressMonth");
if (progressMonthInput && !progressMonthInput.value) {
  progressMonthInput.value = currentMonth();
}

setSessionUserText("sessionUserText");
if (document.getElementById("budgetsOut") && getAccessToken()) {
  loadBudgets();
}
if (document.getElementById("budgetProgressOut") && getAccessToken()) {
  loadBudgetProgress();
}
