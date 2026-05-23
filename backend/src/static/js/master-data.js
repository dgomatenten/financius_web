function setMasterDataJson(id, payload) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = JSON.stringify(payload, null, 2);
  }
}

function redirectOnUnauthorized(result) {
  if (result.status === 401) {
    clearSessionTokens();
    window.location.href = "/login";
    return true;
  }
  return false;
}

async function loadCategories() {
  const result = await sessionProtectedFetch("/api/v1/categories");
  if (redirectOnUnauthorized(result)) return;
  setMasterDataJson("categoriesOut", result);
}

const loadCategoriesBtn = document.getElementById("loadCategoriesBtn");
if (loadCategoriesBtn) {
  loadCategoriesBtn.addEventListener("click", loadCategories);
}

const createCategoryForm = document.getElementById("createCategoryForm");
if (createCategoryForm) {
  createCategoryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      name: document.getElementById("categoryName").value.trim(),
      parentId: document.getElementById("categoryParentId").value.trim() || null,
      needsWants: document.getElementById("categoryNeedsWants").value,
    };

    const result = await sessionProtectedFetch("/api/v1/categories", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (redirectOnUnauthorized(result)) return;
    setMasterDataJson("createCategoryOut", result);
  });
}

async function loadMappings() {
  const result = await sessionProtectedFetch("/api/v1/category-mappings");
  if (redirectOnUnauthorized(result)) return;
  setMasterDataJson("mappingOut", result);
}

const loadMappingsBtn = document.getElementById("loadMappingsBtn");
if (loadMappingsBtn) {
  loadMappingsBtn.addEventListener("click", loadMappings);
}

const correctMappingForm = document.getElementById("correctMappingForm");
if (correctMappingForm) {
  correctMappingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const mappingId = document.getElementById("mappingId").value.trim();
    const categoryId = document.getElementById("mappingCategoryId").value.trim();

    const result = await sessionProtectedFetch(`/api/v1/category-mappings/${mappingId}`, {
      method: "PATCH",
      body: JSON.stringify({ categoryId }),
    });
    if (redirectOnUnauthorized(result)) return;
    setMasterDataJson("mappingOut", result);
  });
}

async function loadShops() {
  const result = await sessionProtectedFetch("/api/v1/shops");
  if (redirectOnUnauthorized(result)) return;
  setMasterDataJson("shopsOut", result);
}

const loadShopsBtn = document.getElementById("loadShopsBtn");
if (loadShopsBtn) {
  loadShopsBtn.addEventListener("click", loadShops);
}

const mergeShopsForm = document.getElementById("mergeShopsForm");
if (mergeShopsForm) {
  mergeShopsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const primaryShopId = document.getElementById("primaryShopId").value.trim();
    const secondaryShopId = document.getElementById("secondaryShopId").value.trim();

    const result = await sessionProtectedFetch(`/api/v1/shops/${primaryShopId}/merge`, {
      method: "POST",
      body: JSON.stringify({ secondaryShopId }),
    });
    if (redirectOnUnauthorized(result)) return;
    setMasterDataJson("mergeShopsOut", result);
  });
}

async function loadCards() {
  const result = await sessionProtectedFetch("/api/v1/cards");
  if (redirectOnUnauthorized(result)) return;
  setMasterDataJson("cardsOut", result);
}

const loadCardsBtn = document.getElementById("loadCardsBtn");
if (loadCardsBtn) {
  loadCardsBtn.addEventListener("click", loadCards);
}

const createCardForm = document.getElementById("createCardForm");
if (createCardForm) {
  createCardForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      nickname: document.getElementById("cardNickname").value.trim(),
      cardType: document.getElementById("cardType").value.trim(),
      network: document.getElementById("cardNetwork").value.trim() || null,
      colorHex: document.getElementById("cardColorHex").value.trim() || null,
    };

    const result = await sessionProtectedFetch("/api/v1/cards", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (redirectOnUnauthorized(result)) return;
    setMasterDataJson("createCardOut", result);
  });
}

const deactivateCardForm = document.getElementById("deactivateCardForm");
if (deactivateCardForm) {
  deactivateCardForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const cardId = document.getElementById("deactivateCardId").value.trim();

    const result = await sessionProtectedFetch(`/api/v1/cards/${cardId}`, {
      method: "PATCH",
    });
    if (redirectOnUnauthorized(result)) return;
    setMasterDataJson("deactivateCardOut", result);
  });
}
