const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("msg");
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    try {
      await api.post("/auth/login", { email, password });
      window.location.href = "/index.html";
    } catch (err) {
      showMessage(msg, err.message);
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("msg");
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    try {
      await api.post("/auth/register", { name, email, password });
      window.location.href = "/index.html";
    } catch (err) {
      showMessage(msg, err.message);
    }
  });
}
