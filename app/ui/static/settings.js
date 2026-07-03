(() => {
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function showResult(el, ok, message) {
    el.classList.remove("hidden", "ok", "err");
    el.classList.add(ok ? "ok" : "err");
    el.textContent = message;
  }

  function renderComponents(components) {
    const labels = {
      vault: "Vault",
      openai: "OpenAI",
      telegram: "Telegram",
      api_key: "API-Key",
    };
    const wrap = document.getElementById("status-components");
    wrap.innerHTML = Object.entries(components)
      .map(
        ([key, ok]) => `<div class="stat">
          <div class="label">${escapeHtml(labels[key] || key)}</div>
          <div class="value">${ok ? '<span class="badge ok">ok</span>' : '<span class="badge err">fehlt</span>'}</div>
        </div>`
      )
      .join("");
  }

  function renderCategories(categories) {
    const rows = Object.entries(categories)
      .map(([cat, folder]) => `<tr><td>${escapeHtml(cat)}</td><td>${escapeHtml(folder)}</td></tr>`)
      .join("");
    document.getElementById("categories-table").innerHTML = `
      <table class="data"><thead><tr><th>Kategorie</th><th>Ordner</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  function renderBackup(backup) {
    const recent = backup.recent.length
      ? `<ul class="chat-sources">${backup.recent.map((n) => `<li>${escapeHtml(n)}</li>`).join("")}</ul>`
      : "<p class=\"empty\">Noch keine Backups in diesem Verzeichnis.</p>";
    document.getElementById("backup-info").innerHTML = `
      <p class="hit-path">Befehl: <code>${escapeHtml(backup.command)}</code></p>
      <p class="hit-path">Verzeichnis: ${escapeHtml(backup.directory)}</p>
      <p class="chat-sources-label">Letzte Backups:</p>${recent}`;
  }

  function renderEdition(edition) {
    document.getElementById("edition-info").innerHTML = `
      <p><strong>${escapeHtml(edition.name)}</strong> — ${escapeHtml(edition.license)}</p>
      <p class="empty">${escapeHtml(edition.description)}</p>`;
  }

  async function load() {
    const res = await fetch("/api/ui/settings");
    if (!res.ok) throw new Error("Einstellungen konnten nicht geladen werden");
    const data = await res.json();

    renderComponents(data.components);
    document.getElementById("vault-path").value = data.vault_host_path || "";
    document.getElementById("openai-model").value = data.openai_model || "";
    document.getElementById("embeddings-enabled").checked = data.embeddings_enabled;
    document.getElementById("telegram-ids").value = data.telegram_allowed_user_ids || "";
    document.getElementById("webhook-url").value = data.seiton_webhook_url || "";
    document.getElementById("openai-masked").textContent = data.openai_key_masked
      ? `Aktuell: ${data.openai_key_masked}`
      : "";
    document.getElementById("api-key-masked").textContent = data.seiton_api_key_masked
      ? `Aktuell: ${data.seiton_api_key_masked}`
      : "";
    renderCategories(data.categories);
    renderBackup(data.backup);
    renderEdition(data.edition);
  }

  async function runTest(check, extra = {}) {
    const resultEl = document.getElementById("test-results");
    resultEl.classList.remove("hidden");
    resultEl.textContent = "Teste …";
    const body = {
      check,
      obsidian_vault_host_path: document.getElementById("vault-path").value.trim() || null,
      openai_api_key: document.getElementById("openai-key").value.trim() || null,
      telegram_bot_token: document.getElementById("telegram-token").value.trim() || null,
      ...extra,
    };
    const res = await fetch("/api/ui/settings/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error("Test fehlgeschlagen");
    const data = await res.json();
    const lines = Object.entries(data.results).map(
      ([name, r]) => `${name}: ${r.ok ? "✓" : "✗"} ${r.message}`
    );
    const allOk = Object.values(data.results).every((r) => r.ok);
    showResult(resultEl, allOk, lines.join("\n"));
  }

  document.getElementById("btn-test-vault").addEventListener("click", () => {
    runTest("vault").catch((err) => alert(err.message));
  });
  document.getElementById("btn-test-openai").addEventListener("click", () => {
    runTest("openai").catch((err) => alert(err.message));
  });
  document.getElementById("btn-test-telegram").addEventListener("click", () => {
    runTest("telegram").catch((err) => alert(err.message));
  });

  document.getElementById("settings-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const resultEl = document.getElementById("save-result");
    const payload = {
      obsidian_vault_host_path: document.getElementById("vault-path").value.trim() || null,
      openai_api_key: document.getElementById("openai-key").value.trim(),
      embeddings_enabled: document.getElementById("embeddings-enabled").checked,
      openai_model: document.getElementById("openai-model").value.trim(),
      telegram_bot_token: document.getElementById("telegram-token").value.trim(),
      telegram_allowed_user_ids: document.getElementById("telegram-ids").value.trim(),
      seiton_api_key: document.getElementById("seiton-api-key").value.trim(),
      seiton_webhook_url: document.getElementById("webhook-url").value.trim(),
    };
    try {
      const res = await fetch("/api/ui/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Speichern fehlgeschlagen");
      showResult(resultEl, true, data.message);
      document.getElementById("openai-key").value = "";
      document.getElementById("telegram-token").value = "";
      document.getElementById("seiton-api-key").value = "";
      await load();
    } catch (err) {
      showResult(resultEl, false, err.message);
    }
  });

  load().catch((err) => {
    document.getElementById("status-components").innerHTML =
      `<p class="empty">${escapeHtml(err.message)}</p>`;
  });
})();
