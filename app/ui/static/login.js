// Login-Seite (E23-1): Passwort → Session-Cookie, dann zum Dashboard.

(() => {
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const button = document.getElementById("login-submit");
    const result = document.getElementById("login-result");
    const password = document.getElementById("login-password").value;

    button.disabled = true;
    result.innerHTML = "";
    try {
      const res = await fetch("/api/ui/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        window.location.href = "/dashboard";
        return;
      }
      const data = await res.json().catch(() => ({}));
      const detail = data.detail || "Login fehlgeschlagen.";
      result.innerHTML = `<p class="capture-err">${escapeHtml(detail)}</p>`;
    } catch (err) {
      result.innerHTML = '<p class="capture-err">Server nicht erreichbar.</p>';
    } finally {
      button.disabled = false;
    }
  });
})();
