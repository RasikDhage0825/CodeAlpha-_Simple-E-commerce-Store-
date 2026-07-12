/**
 * Small fetch wrapper for the JSON API.
 * All requests include cookies so the Flask session works across pages.
 */
const api = {
  async request(path, options = {}) {
    const res = await fetch(`/api${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
    if (!res.ok) {
      const message = (data && data.error) || `Request failed (${res.status})`;
      throw new Error(message);
    }
    return data;
  },
  get(path) {
    return this.request(path);
  },
  post(path, body) {
    return this.request(path, { method: "POST", body: JSON.stringify(body || {}) });
  },
  put(path, body) {
    return this.request(path, { method: "PUT", body: JSON.stringify(body || {}) });
  },
  delete(path) {
    return this.request(path, { method: "DELETE" });
  },
};

function formatPrice(n) {
  return `$${Number(n).toFixed(2)}`;
}

/**
 * Populates the shared header: shows login/register or the user's name + logout,
 * and keeps the cart item-count badge up to date. Every page calls this on load.
 */
async function initHeader() {
  const authArea = document.getElementById("auth-area");
  const cartBadge = document.getElementById("cart-badge");
  if (!authArea) return;

  try {
    const { user } = await api.get("/auth/me");
    if (user) {
      authArea.innerHTML = `
        <span>Hi, ${escapeHtml(user.name)}</span>
        <button id="logout-btn">Log out</button>
      `;
      document.getElementById("logout-btn").addEventListener("click", async () => {
        await api.post("/auth/logout");
        window.location.href = "/index.html";
      });

      if (cartBadge) {
        try {
          const cart = await api.get("/cart");
          const count = cart.items.reduce((sum, i) => sum + i.quantity, 0);
          if (count > 0) {
            cartBadge.textContent = count;
            cartBadge.classList.remove("hidden");
          }
        } catch (e) {
          /* not fatal if cart count fails */
        }
      }
    } else {
      authArea.innerHTML = `
        <a href="/login.html">Log in</a>
        <a href="/register.html">Sign up</a>
      `;
    }
  } catch (e) {
    authArea.innerHTML = `<a href="/login.html">Log in</a> <a href="/register.html">Sign up</a>`;
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showMessage(el, message, isError = true) {
  if (!el) return;
  el.textContent = message;
  el.style.display = "block";
  el.className = isError ? "error-msg" : "success-msg";
  el.style.display = "block";
}

document.addEventListener("DOMContentLoaded", initHeader);
