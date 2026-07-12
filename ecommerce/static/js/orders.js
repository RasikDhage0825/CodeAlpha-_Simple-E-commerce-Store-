const ordersContainer = document.getElementById("orders-container");
const placedMsg = document.getElementById("placed-msg");

const placedOrderId = new URLSearchParams(window.location.search).get("placed");
if (placedOrderId) {
  placedMsg.textContent = `Order #${placedOrderId} placed successfully! Thank you for your purchase.`;
  placedMsg.style.display = "block";
}

async function loadOrders() {
  try {
    const data = await api.get("/orders");
    renderOrders(data.orders);
  } catch (e) {
    if (e.message.includes("Authentication")) {
      ordersContainer.innerHTML = `<p class="empty-state">Please <a href="/login.html">log in</a> to see your orders.</p>`;
    } else {
      ordersContainer.innerHTML = `<p class="empty-state">Couldn't load orders.</p>`;
    }
  }
}

function renderOrders(orders) {
  if (orders.length === 0) {
    ordersContainer.innerHTML = `
      <div class="empty-state">
        <p>You haven't placed any orders yet.</p>
        <a href="/index.html" class="btn btn-primary">Start shopping</a>
      </div>
    `;
    return;
  }

  ordersContainer.innerHTML = orders.map(order => `
    <div class="order-card">
      <div class="order-card-header">
        <div>
          <strong>Order #${order.id}</strong>
          <span class="muted"> — ${new Date(order.created_at).toLocaleDateString()}</span>
        </div>
        <span class="order-status">${escapeHtml(order.status)}</span>
      </div>
      <div class="muted" style="margin-bottom:8px;">Shipping to: ${escapeHtml(order.shipping_address || "")}</div>
      ${order.items.map(item => `
        <div class="order-item-row">
          <span>${escapeHtml(item.product_name)} × ${item.quantity}</span>
          <span>${formatPrice(item.price * item.quantity)}</span>
        </div>
      `).join("")}
      <div class="order-item-row" style="font-weight:700; color:var(--color-text); border-top:1px solid var(--color-border); margin-top:8px; padding-top:8px;">
        <span>Total</span>
        <span>${formatPrice(order.total)}</span>
      </div>
    </div>
  `).join("");
}

loadOrders();
