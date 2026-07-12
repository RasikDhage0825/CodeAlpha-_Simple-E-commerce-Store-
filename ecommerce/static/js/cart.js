const cartContainer = document.getElementById("cart-container");
const checkoutPanel = document.getElementById("checkout-panel");

async function loadCart() {
  try {
    const me = await api.get("/auth/me");
    if (!me.user) {
      cartContainer.innerHTML = `
        <p class="empty-state">Please <a href="/login.html">log in</a> to view your cart.</p>
      `;
      return;
    }
  } catch (e) { /* proceed, /cart will 401 if not logged in */ }

  try {
    const data = await api.get("/cart");
    renderCart(data.items, data.total);
  } catch (e) {
    if (e.message.includes("Authentication")) {
      cartContainer.innerHTML = `
        <p class="empty-state">Please <a href="/login.html">log in</a> to view your cart.</p>
      `;
    } else {
      cartContainer.innerHTML = `<p class="empty-state">Couldn't load your cart.</p>`;
    }
  }
}

function renderCart(items, total) {
  if (items.length === 0) {
    cartContainer.innerHTML = `
      <div class="empty-state">
        <p>Your cart is empty.</p>
        <a href="/index.html" class="btn btn-primary">Browse products</a>
      </div>
    `;
    checkoutPanel.classList.add("hidden");
    return;
  }

  cartContainer.innerHTML = items.map(item => `
    <div class="cart-item" data-id="${item.cart_item_id}">
      <img src="${item.image_url}" alt="${escapeHtml(item.name)}">
      <div>
        <div class="cart-item-name">${escapeHtml(item.name)}</div>
        <div class="cart-item-price">${formatPrice(item.price)} each</div>
      </div>
      <div class="qty-control">
        <button class="decr-btn">-</button>
        <span class="qty-val">${item.quantity}</span>
        <button class="incr-btn">+</button>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:600;">${formatPrice(item.price * item.quantity)}</div>
        <button class="btn btn-danger remove-btn">Remove</button>
      </div>
    </div>
  `).join("") + `
    <div class="cart-summary">
      <span class="cart-total">Total: ${formatPrice(total)}</span>
      <button id="checkout-btn" class="btn btn-accent">Checkout</button>
    </div>
  `;

  checkoutPanel.classList.add("hidden");

  cartContainer.querySelectorAll(".cart-item").forEach(el => {
    const id = el.dataset.id;
    const qtyVal = el.querySelector(".qty-val");

    el.querySelector(".incr-btn").addEventListener("click", async () => {
      const newQty = parseInt(qtyVal.textContent, 10) + 1;
      await updateQty(id, newQty);
    });
    el.querySelector(".decr-btn").addEventListener("click", async () => {
      const newQty = parseInt(qtyVal.textContent, 10) - 1;
      await updateQty(id, newQty);
    });
    el.querySelector(".remove-btn").addEventListener("click", async () => {
      await api.delete(`/cart/${id}`);
      loadCart();
    });
  });

  document.getElementById("checkout-btn").addEventListener("click", () => {
    checkoutPanel.classList.remove("hidden");
    checkoutPanel.scrollIntoView({ behavior: "smooth" });
  });
}

async function updateQty(id, newQty) {
  try {
    await api.put(`/cart/${id}`, { quantity: newQty });
    loadCart();
  } catch (e) {
    alert(e.message);
  }
}

document.getElementById("place-order-btn").addEventListener("click", async () => {
  const address = document.getElementById("address").value.trim();
  const msg = document.getElementById("checkout-msg");
  if (!address) {
    showMessage(msg, "Please enter a shipping address.");
    return;
  }
  try {
    const result = await api.post("/orders", { shipping_address: address });
    window.location.href = `/orders.html?placed=${result.order_id}`;
  } catch (e) {
    showMessage(msg, e.message);
  }
});

loadCart();
