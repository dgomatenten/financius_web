function setJson(id, payload) {
  const el = document.getElementById(id);
  el.textContent = JSON.stringify(payload, null, 2);
}

async function callApi(path, options = {}) {
  const token = localStorage.getItem("accessToken");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });
  const json = await res.json();
  return { status: res.status, body: json };
}

document.getElementById("healthBtn").addEventListener("click", async () => {
  try {
    const result = await callApi("/api/v1/health");
    setJson("healthOut", result);
  } catch (error) {
    setJson("healthOut", { error: String(error) });
  }
});

document.getElementById("loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();

  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  try {
    const result = await callApi("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    const accessToken = result.body?.data?.accessToken;
    if (accessToken) {
      localStorage.setItem("accessToken", accessToken);
    }

    setJson("loginOut", result);
  } catch (error) {
    setJson("loginOut", { error: String(error) });
  }
});

document.getElementById("syncBtn").addEventListener("click", async () => {
  try {
    const result = await callApi("/api/v1/sync/status", { method: "GET" });
    setJson("syncOut", result);
  } catch (error) {
    setJson("syncOut", { error: String(error) });
  }
});
