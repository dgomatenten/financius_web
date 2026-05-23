function asMoney(value, currency) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: currency || "USD",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function asPct(value) {
  const num = Number(value || 0);
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(2)}%`;
}

function setStatus(message) {
  const status = document.getElementById("analyticsStatus");
  if (status) {
    status.textContent = message;
  }
}

function getData(result) {
  return result?.body?.data || null;
}

function chipClassForDelta(value) {
  const num = Number(value || 0);
  if (num > 3) {
    return "bad";
  }
  if (num < -3) {
    return "ok";
  }
  return "warn";
}

function renderKpis(summary) {
  const wrap = document.getElementById("analyticsKpis");
  if (!wrap) {
    return;
  }
  const total = summary?.totalSpending || 0;
  const count = summary?.receiptCount || 0;
  const mom = summary?.monthOverMonthPct || 0;
  const avg = count > 0 ? total / count : 0;
  const currency = summary?.currency || "USD";

  wrap.innerHTML = "";
  const items = [
    ["Total Spending", asMoney(total, currency), `Period: ${summary?.period || "this_month"}`],
    ["Receipts", String(count), "Transactions in selected period"],
    ["MoM Delta", asPct(mom), "Compared to previous window"],
    ["Avg Per Receipt", asMoney(avg, currency), "Total / receipt count"],
  ];

  for (const [label, value, sub] of items) {
    const card = document.createElement("article");
    card.className = "kpi-card";
    card.innerHTML = `<span class="kpi-label">${label}</span><div class="kpi-value">${value}</div><div class="kpi-sub">${sub}</div>`;
    wrap.appendChild(card);
  }
}

function renderRankList(elementId, rows, amountKey, currency) {
  const list = document.getElementById(elementId);
  if (!list) {
    return;
  }
  list.innerHTML = "";

  if (!rows || rows.length === 0) {
    list.innerHTML = "<li class='muted'>No data for the selected period.</li>";
    return;
  }

  const max = Math.max(...rows.map((r) => Number(r[amountKey] || 0)), 0);
  for (const row of rows) {
    const amount = Number(row[amountKey] || 0);
    const pct = max > 0 ? (amount / max) * 100 : 0;
    const item = document.createElement("li");
    item.innerHTML = `
      <div class="row-split">
        <strong>${row.name || "Unknown"}</strong>
        <span>${asMoney(amount, currency)}</span>
      </div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct.toFixed(1)}%"></div></div>
    `;
    list.appendChild(item);
  }
}

function tableHtml(columns, rows) {
  if (!rows || rows.length === 0) {
    return "<p class='muted'>No rows available.</p>";
  }
  const header = columns.map((c) => `<th>${c.label}</th>`).join("");
  const body = rows
    .map((row) => {
      const cells = columns.map((c) => `<td>${c.render(row)}</td>`).join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");
  return `<table class="viz-table"><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
}

function renderCalendar(days, currency) {
  const wrap = document.getElementById("analyticsCalendarTable");
  if (!wrap) {
    return;
  }
  wrap.innerHTML = tableHtml(
    [
      { label: "Day", render: (r) => r.day || "-" },
      { label: "Spend", render: (r) => asMoney(r.amount || 0, currency) },
      { label: "Receipts", render: (r) => String(r.receiptCount || 0) },
    ],
    days
  );
}

function renderYoy(items, currency) {
  const wrap = document.getElementById("analyticsYoyTable");
  if (!wrap) {
    return;
  }
  wrap.innerHTML = tableHtml(
    [
      { label: "Category", render: (r) => r.name || "Uncategorized" },
      { label: "Current", render: (r) => asMoney(r.current || 0, currency) },
      { label: "Previous", render: (r) => asMoney(r.previous || 0, currency) },
      {
        label: "Change",
        render: (r) => {
          const klass = chipClassForDelta(r.changePct);
          return `<span class="chip ${klass}">${asPct(r.changePct)}</span>`;
        },
      },
    ],
    items
  );
}

function renderBls(items, currency) {
  const wrap = document.getElementById("analyticsBlsTable");
  if (!wrap) {
    return;
  }
  wrap.innerHTML = tableHtml(
    [
      { label: "Category", render: (r) => r.name || "Uncategorized" },
      { label: "Spend", render: (r) => asMoney(r.amount || 0, currency) },
      { label: "Your Share", render: (r) => asPct(r.userSharePct) },
      { label: "Benchmark", render: (r) => asPct(r.benchmarkSharePct) },
      {
        label: "Delta",
        render: (r) => {
          const klass = chipClassForDelta(r.deltaPct);
          return `<span class="chip ${klass}">${asPct(r.deltaPct)}</span>`;
        },
      },
    ],
    items
  );
}

function renderInsights(insights) {
  const wrap = document.getElementById("analyticsInsightsTags");
  if (!wrap) {
    return;
  }
  wrap.innerHTML = "";
  if (!insights || insights.length === 0) {
    wrap.innerHTML = "<p class='muted'>No insights available.</p>";
    return;
  }

  for (const item of insights) {
    const tag = document.createElement("span");
    tag.className = "metric-tag";
    tag.textContent = `${item.label}: ${item.value}`;
    wrap.appendChild(tag);
  }
}

function analyticsParams() {
  const period = document.getElementById("analyticsPeriod")?.value || "this_month";
  const currency = document.getElementById("analyticsCurrency")?.value || "USD";
  return new URLSearchParams({ period, currency }).toString();
}

async function loadAnalytics() {
  setStatus("Loading analytics...");
  const params = analyticsParams();

  const requests = {
    summary: sessionProtectedFetch(`/api/v1/analytics/summary?${params}`),
    breakdown: sessionProtectedFetch(`/api/v1/analytics/category-breakdown?${params}`),
    calendar: sessionProtectedFetch(`/api/v1/analytics/calendar?${params}`),
    yoy: sessionProtectedFetch(`/api/v1/analytics/yoy?${params}`),
    bls: sessionProtectedFetch(`/api/v1/analytics/benchmarks/bls?${params}`),
    insights: sessionProtectedFetch(`/api/v1/analytics/insights?${params}`),
  };

  const [summaryRes, breakdownRes, calendarRes, yoyRes, blsRes, insightsRes] = await Promise.all([
    requests.summary,
    requests.breakdown,
    requests.calendar,
    requests.yoy,
    requests.bls,
    requests.insights,
  ]);

  const responses = [summaryRes, breakdownRes, calendarRes, yoyRes, blsRes, insightsRes];
  if (responses.some((r) => r.status === 401)) {
    clearSessionTokens();
    window.location.href = "/login";
    return;
  }

  if (responses.some((r) => !r.ok)) {
    setStatus("Some analytics endpoints failed. Please try again.");
    return;
  }

  const summary = getData(summaryRes) || {};
  const breakdownData = getData(breakdownRes) || {};
  const calendarData = getData(calendarRes) || {};
  const yoyData = getData(yoyRes) || {};
  const blsData = getData(blsRes) || {};
  const insightsData = getData(insightsRes) || {};

  const currency = summary.currency || document.getElementById("analyticsCurrency")?.value || "USD";

  renderKpis(summary);
  renderRankList("analyticsCategoryList", summary.topCategories || breakdownData.items || [], "amount", currency);
  renderRankList("analyticsShopList", summary.topShops || [], "amount", currency);
  renderCalendar(calendarData.days || [], currency);
  renderYoy(yoyData.items || [], currency);
  renderBls(blsData.items || [], currency);
  renderInsights(insightsData.insights || []);
  setStatus("Updated just now.");
}

const analyticsFilters = document.getElementById("analyticsFilters");
if (analyticsFilters) {
  analyticsFilters.addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadAnalytics();
  });
}

setSessionUserText("sessionUserText");
if (getAccessToken()) {
  loadAnalytics();
}
