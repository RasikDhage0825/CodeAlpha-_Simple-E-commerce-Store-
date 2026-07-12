const grid = document.getElementById("product-grid");
const emptyMsg = document.getElementById("empty-msg");
const searchInput = document.getElementById("search-input");
const categorySelect = document.getElementById("category-select");

let searchTimer = null;

function renderProducts(products) {
  grid.innerHTML = "";
  emptyMsg.classList.toggle("hidden", products.length > 0);

  for (const p of products) {
    const card = document.createElement("a");
    card.href = `/product.html?id=${p.id}`;
    card.className = "product-card";
    card.innerHTML = `
      <img src="${p.image_url}" alt="${escapeHtml(p.name)}" loading="lazy">
      <div class="product-card-body">
        <span class="product-category">${escapeHtml(p.category)}</span>
        <span class="product-name">${escapeHtml(p.name)}</span>
        <span class="product-price">${formatPrice(p.price)}</span>
      </div>
    `;
    grid.appendChild(card);
  }
}

function populateCategories(categories) {
  const current = categorySelect.value;
  categorySelect.innerHTML = `<option value="">All categories</option>`;
  for (const c of categories) {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    categorySelect.appendChild(opt);
  }
  categorySelect.value = current;
}

async function loadProducts() {
  const params = new URLSearchParams();
  if (searchInput.value.trim()) params.set("search", searchInput.value.trim());
  if (categorySelect.value) params.set("category", categorySelect.value);

  try {
    const data = await api.get(`/products?${params.toString()}`);
    renderProducts(data.products);
    populateCategories(data.categories);
  } catch (e) {
    grid.innerHTML = `<p class="empty-state">Couldn't load products: ${escapeHtml(e.message)}</p>`;
  }
}

searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadProducts, 300);
});
categorySelect.addEventListener("change", loadProducts);

loadProducts();
