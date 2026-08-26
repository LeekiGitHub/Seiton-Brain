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

  function renderNoteTemplate(status, path) {
    const el = document.getElementById("note-template-info");
    if (!el) return;
    let badge;
    if (status === "custom") {
      badge = '<span class="badge ok">eigenes Template aktiv</span>';
    } else if (status === "invalid") {
      badge = '<span class="badge err">Template ungültig — Default-Layout aktiv (Details im Log)</span>';
    } else {
      badge = '<span class="badge">Default-Layout</span>';
    }
    el.innerHTML = `<p class="hit-path">Notiz-Template (E26): ${badge} · Datei: <code>${escapeHtml(path)}</code> im Vault ·
      Platzhalter: <code>{{title}}</code> <code>{{summary}}</code> <code>{{tags}}</code> <code>{{date}}</code> <code>{{category}}</code> <code>{{related}}</code></p>`;
  }

  function renderBackup(backup) {
    document.getElementById("backup-info").innerHTML = `
      <p class="hit-path">Verzeichnis: ${escapeHtml(backup.directory)} · Alternativ per Terminal: <code>${escapeHtml(backup.command)}</code></p>`;
  }

  function formatBytes(n) {
    if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
    if (n >= 1024) return `${(n / 1024).toFixed(0)} KB`;
    return `${n} B`;
  }

  function renderBackupList(data) {
    const wrap = document.getElementById("backup-list");
    if (!data.items.length) {
      wrap.innerHTML = '<p class="empty">Noch keine Backups in diesem Verzeichnis.</p>';
      return;
    }
    const rows = data.items
      .map((b) => {
        const files = Object.entries(b.files)
          .map(([name, size]) => `${escapeHtml(name)} (${formatBytes(size)})`)
          .join(" · ");
        const restore = b.restore.map((c) => escapeHtml(c)).join("\n");
        return `<details class="backup-item">
          <summary><strong>${escapeHtml(b.name)}</strong> — ${files}</summary>
          <p class="chat-sources-label">Restore (Terminal, überschreibt bestehende Daten):</p>
          <pre class="restore-cmds"><code>${restore}</code></pre>
        </details>`;
      })
      .join("");
    wrap.innerHTML = `<p class="chat-sources-label">Vorhandene Backups:</p>${rows}`;
  }

  async function loadBackups() {
    try {
      const res = await fetch("/api/ui/backups");
      if (!res.ok) throw new Error("Backups konnten nicht geladen werden");
      renderBackupList(await res.json());
    } catch (err) {
      document.getElementById("backup-list").innerHTML =
        `<p class="empty">${escapeHtml(err.message)}</p>`;
    }
  }

  document.getElementById("btn-backup").addEventListener("click", async () => {
    const btn = document.getElementById("btn-backup");
    const resultEl = document.getElementById("backup-result");
    btn.disabled = true;
    resultEl.innerHTML = '<p class="empty">Erstelle Backup (Datenbank + Vault) …</p>';
    try {
      const res = await fetch("/api/ui/backup", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Backup fehlgeschlagen");
      const warn = data.warnings.length
        ? ` <span class="badge warn">${escapeHtml(data.warnings.join(" "))}</span>`
        : "";
      resultEl.innerHTML = `<p class="capture-ok"><span class="badge ok">ok</span>
        Backup <strong>${escapeHtml(data.name)}</strong> erstellt.${warn}</p>`;
      await loadBackups();
    } catch (err) {
      resultEl.innerHTML = `<p class="capture-err">${escapeHtml(err.message)}</p>`;
    } finally {
      btn.disabled = false;
    }
  });

  document.getElementById("btn-reindex").addEventListener("click", async () => {
    const btn = document.getElementById("btn-reindex");
    const resultEl = document.getElementById("reindex-result");
    btn.disabled = true;
    resultEl.innerHTML = '<p class="empty">Indexiere Vault …</p>';
    try {
      const res = await fetch("/api/ui/reindex?full=true", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Indexierung fehlgeschlagen");
      resultEl.innerHTML = `<p class="capture-ok"><span class="badge ok">ok</span>
        ${escapeHtml(data.message)}</p>`;
    } catch (err) {
      resultEl.innerHTML = `<p class="capture-err">${escapeHtml(err.message)}</p>`;
    } finally {
      btn.disabled = false;
    }
  });

  function renderEdition(edition) {
    document.getElementById("edition-info").innerHTML = `
      <p><strong>${escapeHtml(edition.name)}</strong> — ${escapeHtml(edition.license)}</p>
      <p class="empty">${escapeHtml(edition.description)}</p>`;
  }

  function renderLicense(license) {
    const badge = license.valid
      ? '<span class="badge ok">gültig</span>'
      : license.key_masked
        ? '<span class="badge err">ungültig</span>'
        : '<span class="badge">keine</span>';
    const expires = license.expires ? ` · gültig bis ${license.expires}` : "";
    document.getElementById("license-status").innerHTML = `
      <p>${badge} ${escapeHtml(license.message || "")}${escapeHtml(expires)}</p>
      ${license.licensee ? `<p class="hit-path">Lizenznehmer: ${escapeHtml(license.licensee)}</p>` : ""}`;
    document.getElementById("license-masked").textContent = license.key_masked
      ? `Aktuell: ${license.key_masked}`
      : "";
    if (license.required && !license.valid) {
      document.getElementById("license-status").innerHTML +=
        '<p class="empty">SEITON_LICENSE_REQUIRED=true — Prozess startet nur mit gültiger Lizenz.</p>';
    }
  }

  async function loadLicense() {
    const res = await fetch("/api/ui/license");
    if (!res.ok) throw new Error("Lizenzstatus konnte nicht geladen werden");
    const data = await res.json();
    renderLicense(data);
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
    renderNoteTemplate(data.note_template, data.note_template_path);
    renderBackup(data.backup);
    renderEdition(data.edition);
    await loadLicense();
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

  document.getElementById("btn-save-license").addEventListener("click", async () => {
    const resultEl = document.getElementById("license-result");
    const key = document.getElementById("license-key").value.trim();
    if (!key) {
      showResult(resultEl, false, "Bitte Lizenzschlüssel eingeben");
      return;
    }
    try {
      const res = await fetch("/api/ui/license", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ license_key: key }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Speichern fehlgeschlagen");
      showResult(resultEl, true, data.message);
      document.getElementById("license-key").value = "";
      await load();
    } catch (err) {
      showResult(resultEl, false, err.message);
    }
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
  loadBackups();
})();
