(() => {
  let currentStep = 0;
  const panels = document.querySelectorAll(".step-panel");
  const dots = document.querySelectorAll(".step-dot");

  function showStep(n) {
    currentStep = n;
    panels.forEach((p) => p.classList.toggle("hidden", Number(p.dataset.step) !== n));
    dots.forEach((d) => {
      const i = Number(d.dataset.step);
      d.classList.toggle("active", i === n);
      d.classList.toggle("done", i < n);
    });
    if (n === 4) renderSummary();
  }

  function showResult(el, ok, message) {
    el.textContent = message;
    el.classList.remove("hidden", "ok", "err");
    el.classList.add(ok ? "ok" : "err");
  }

  async function api(path, options = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || res.statusText);
    }
    return data;
  }

  function payload() {
    return {
      obsidian_vault_host_path: document.getElementById("vault-path").value.trim(),
      openai_api_key: document.getElementById("openai-key").value.trim(),
      telegram_bot_token: document.getElementById("telegram-enable").checked
        ? document.getElementById("telegram-token").value.trim()
        : "",
      telegram_webhook_secret: document.getElementById("telegram-secret").value.trim(),
      telegram_allowed_user_ids: document.getElementById("telegram-allowlist").value.trim(),
      embeddings_enabled: document.getElementById("embeddings-enabled").checked,
    };
  }

  async function loadStatus() {
    try {
      const status = await api("/api/setup/status");
      const el = document.getElementById("status-summary");
      const parts = Object.entries(status.components)
        .map(([k, v]) => `${k}: ${v ? "✓" : "—"}`)
        .join(" · ");
      el.textContent = `Status: ${parts}`;
    } catch {
      /* ignore on first paint */
    }
  }

  function renderSummary() {
    const p = payload();
    const lines = [
      `Vault: ${p.obsidian_vault_host_path || "—"}`,
      `OpenAI: ${p.openai_api_key ? "••••" + p.openai_api_key.slice(-4) : "—"}`,
      `Embeddings: ${p.embeddings_enabled ? "an" : "aus"}`,
      `Telegram: ${p.telegram_bot_token ? "ja" : "übersprungen"}`,
    ];
    document.getElementById("summary").innerHTML = lines.join("<br>");
  }

  document.getElementById("btn-start").addEventListener("click", () => showStep(1));

  document.querySelectorAll(".btn-back").forEach((btn) => {
    btn.addEventListener("click", () => showStep(Math.max(0, currentStep - 1)));
  });

  document.querySelectorAll(".btn-next").forEach((btn) => {
    btn.addEventListener("click", () => showStep(Math.min(4, currentStep + 1)));
  });

  document.getElementById("telegram-enable").addEventListener("change", (e) => {
    document.getElementById("telegram-fields").classList.toggle("hidden", !e.target.checked);
  });

  document.getElementById("btn-test-vault").addEventListener("click", async () => {
    const el = document.getElementById("result-vault");
    try {
      const body = { check: "vault", obsidian_vault_host_path: document.getElementById("vault-path").value.trim() };
      const data = await api("/api/setup/test", { method: "POST", body: JSON.stringify(body) });
      const r = data.results.vault;
      showResult(el, r.ok, r.message);
    } catch (err) {
      showResult(el, false, String(err.message));
    }
  });

  document.getElementById("btn-test-openai").addEventListener("click", async () => {
    const el = document.getElementById("result-openai");
    try {
      const body = { check: "openai", openai_api_key: document.getElementById("openai-key").value.trim() };
      const data = await api("/api/setup/test", { method: "POST", body: JSON.stringify(body) });
      const r = data.results.openai;
      showResult(el, r.ok, r.message);
    } catch (err) {
      showResult(el, false, String(err.message));
    }
  });

  document.getElementById("btn-test-telegram").addEventListener("click", async () => {
    const el = document.getElementById("result-telegram");
    try {
      const body = { check: "telegram", telegram_bot_token: document.getElementById("telegram-token").value.trim() };
      const data = await api("/api/setup/test", { method: "POST", body: JSON.stringify(body) });
      const r = data.results.telegram;
      showResult(el, r.ok, r.message);
    } catch (err) {
      showResult(el, false, String(err.message));
    }
  });

  document.getElementById("btn-test-all").addEventListener("click", async () => {
    const el = document.getElementById("result-save");
    try {
      const p = payload();
      const body = { check: "all", ...p };
      const data = await api("/api/setup/test", { method: "POST", body: JSON.stringify(body) });
      const lines = Object.entries(data.results).map(([k, v]) => `${k}: ${v.message}`);
      const allOk = Object.values(data.results).every((r) => r.ok);
      showResult(el, allOk, lines.join("\n"));
    } catch (err) {
      showResult(el, false, String(err.message));
    }
  });

  document.getElementById("btn-save").addEventListener("click", async () => {
    const el = document.getElementById("result-save");
    const btn = document.getElementById("btn-save");
    btn.disabled = true;
    try {
      const data = await api("/api/setup/save", {
        method: "POST",
        body: JSON.stringify(payload()),
      });
      showResult(el, true, data.message + "\nDatei: " + data.env_file);
    } catch (err) {
      showResult(el, false, String(err.message));
    } finally {
      btn.disabled = false;
    }
  });

  loadStatus();
})();
