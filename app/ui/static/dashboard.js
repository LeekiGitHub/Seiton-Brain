(() => {
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function badge(status) {
    const cls =
      status === "failed" || status === "rejected"
        ? "err"
        : status === "appended"
          ? "warn"
          : "ok";
    return `<span class="badge ${cls}">${escapeHtml(status)}</span>`;
  }

  function formatDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleString("de-DE", {
      dateStyle: "short",
      timeStyle: "short",
    });
  }

  function renderEntries(items) {
    const wrap = document.getElementById("entries-table-wrap");
    if (!items.length) {
      wrap.innerHTML = '<p class="empty">Noch keine Entries — sende eine Nachricht an den Bot oder nutze Capture.</p>';
      return;
    }
    const rows = items
      .map(
        (e) => `<tr>
          <td>${formatDate(e.created_at)}</td>
          <td class="truncate" title="${escapeHtml(e.title)}">${escapeHtml(e.title)}</td>
          <td>${escapeHtml(e.category || "—")}</td>
          <td>${escapeHtml(e.kind)}</td>
          <td>${badge(e.status)}</td>
        </tr>`
      )
      .join("");
    wrap.innerHTML = `<table class="data"><thead><tr>
      <th>Zeit</th><th>Titel</th><th>Kategorie</th><th>Art</th><th>Status</th>
    </tr></thead><tbody>${rows}</tbody></table>`;
  }

  function renderVault(items) {
    const wrap = document.getElementById("vault-table-wrap");
    if (!items.length) {
      wrap.innerHTML = '<p class="empty">Noch keine indexierten Notizen im Vault.</p>';
      return;
    }
    const rows = items
      .map(
        (n) => `<tr>
          <td>${formatDate(n.mtime)}</td>
          <td class="truncate" title="${escapeHtml(n.title)}">${escapeHtml(n.title)}</td>
          <td>${escapeHtml(n.folder)}</td>
          <td class="truncate" title="${escapeHtml(n.vault_path)}">${escapeHtml(n.vault_path)}</td>
        </tr>`
      )
      .join("");
    wrap.innerHTML = `<table class="data"><thead><tr>
      <th>Geändert</th><th>Titel</th><th>Ordner</th><th>Pfad</th>
    </tr></thead><tbody>${rows}</tbody></table>`;
  }

  function renderStats(stats) {
    document.getElementById("stat-total").textContent = String(stats.total_entries);
    document.getElementById("stat-vault").textContent = String(stats.vault_notes_indexed);
    const text = stats.entries_by_kind.text || 0;
    const voice = stats.entries_by_kind.voice || 0;
    document.getElementById("stat-kind").textContent = `${text} / ${voice}`;
    document.getElementById("stat-embed").innerHTML = stats.embeddings_enabled
      ? '<span class="badge ok">an</span>'
      : '<span class="badge muted">aus</span>';

    const parts = Object.entries(stats.entries_by_status)
      .filter(([, n]) => n > 0)
      .map(([k, n]) => `${k}: ${n}`);
    document.getElementById("stat-status").textContent = parts.length
      ? `Status: ${parts.join(" · ")}`
      : "";
  }

  async function load() {
    const res = await fetch("/api/ui/dashboard");
    if (!res.ok) throw new Error("Dashboard konnte nicht geladen werden");
    const data = await res.json();
    renderStats(data.stats);
    renderEntries(data.recent_entries);
    renderVault(data.recent_vault_notes);
  }

  async function capture(text) {
    const res = await fetch("/api/ui/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      let detail = "Capture fehlgeschlagen";
      try {
        detail = (await res.json()).detail || detail;
      } catch {
        /* Antwort ohne JSON-Body */
      }
      throw new Error(detail);
    }
    return res.json();
  }

  document.getElementById("capture-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const textEl = document.getElementById("capture-text");
    const text = textEl.value.trim();
    if (!text) return;

    const submitBtn = document.getElementById("capture-submit");
    const resultEl = document.getElementById("capture-result");
    submitBtn.disabled = true;
    resultEl.innerHTML = '<p class="empty">Klassifiziere und speichere …</p>';

    try {
      const data = await capture(text);
      const actionLabel = data.action === "append" ? "ergänzt" : "neu angelegt";
      const tags = data.tags.length
        ? ` · ${data.tags.map((t) => `#${escapeHtml(t)}`).join(" ")}`
        : "";
      resultEl.innerHTML = `<p class="capture-ok">${badge(data.status)}
        <strong>${escapeHtml(data.title)}</strong> (${escapeHtml(data.category)}, ${escapeHtml(actionLabel)})
        <span class="hit-path">${escapeHtml(data.vault_path)}</span>${tags}</p>`;
      textEl.value = "";
      await load();
    } catch (err) {
      resultEl.innerHTML = `<p class="capture-err">${escapeHtml(err.message)}</p>`;
    } finally {
      submitBtn.disabled = false;
    }
  });

  document.getElementById("capture-text").addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      document.getElementById("capture-form").requestSubmit();
    }
  });

  document.getElementById("btn-refresh").addEventListener("click", () => {
    load().catch((err) => alert(err.message));
  });

  load().catch((err) => {
    document.getElementById("entries-table-wrap").innerHTML =
      `<p class="empty">${escapeHtml(err.message)}</p>`;
  });
})();
