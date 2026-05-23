function setImportJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

const amazonImportForm = document.getElementById("amazonImportForm");
if (amazonImportForm) {
  amazonImportForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const fileInput = document.getElementById("amazonCsvFile");
    const file = fileInput?.files?.[0];
    if (!file) {
      setImportJson("importOut", { error: "Please choose a CSV file" });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const accessToken = getAccessToken();
    const headers = {};
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`;
    }

    const response = await fetch("/api/v1/receipts/import/amazon", {
      method: "POST",
      headers,
      body: formData,
    });

    let body = null;
    try {
      body = await response.json();
    } catch (_error) {
      body = null;
    }

    if (response.status === 401) {
      clearSessionTokens();
      window.location.href = "/login";
      return;
    }

    setImportJson("importOut", { status: response.status, body });
  });
}
