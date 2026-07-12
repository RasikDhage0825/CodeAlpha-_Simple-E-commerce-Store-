const container = document.getElementById("product-container");
const productId = new URLSearchParams(window.location.search).get("id");

async function loadProduct() {
  if (!productId) {
    container.innerHTML = `<p class="empty-state">No product specified.</p>`;
    return;
  }
  try {
    const p = await api.get(`/products/${productId}`);
    renderProduct(p);
  } catch (e) {
    container.innerHTML = `<p class="empty-state">Product not found.</p>`;
  }
}

function renderProduct(p) {
  const inStock = p.stock > 0;
  container.innerHTML = `
    <div class="product-detail">
      <img src="${p.image_url}" alt="${escapeHtml(p.name)}">
      <div>
        <span class="product-category">${escapeHtml(p.category)}</span>
        <h1 style="margin:6px 0;">${escapeHtml(p.name)}</h1>
        <p class="product-price">${formatPrice(p.price)}</p>
        <p>${escapeHtml(p.description)}</p>
        <p class="stock-note">${inStock ? `${p.stock} in stock` : "Out of stock"}</p>

        <div id="msg" class="error-msg"></div>

        <div class="qty-row">
          <label for="qty">Qty</label>
          <input type="number" id="qty" value="1" min="1" max="${p.stock}" ${inStock ? "" : "disabled"}>
          <button id="add-btn" class="btn btn-primary" ${inStock ? "" : "disabled"}>Add to Cart</button>
        </div>
        <a href="/index.html" class="btn btn-outline">&larr; Back to shop</a>
      </div>
    </div>
  `;

  const addBtn = document.getElementById("add-btn");
  const msg = document.getElementById("msg");

  addBtn.addEventListener("click", async () => {
    const qty = parseInt(document.getElementById("qty").value, 10) || 1;
    addBtn.disabled = true;
    try {
      await api.post("/cart", { product_id: p.id, quantity: qty });
      window.location.href = "/cart.html";
    } catch (e) {
      if (e.message.includes("Authentication")) {
        window.location.href = "/login.html";
        return;
      }
      showMessage(msg, e.message, true);
      addBtn.disabled = false;
    }
  });
}

loadProduct();
