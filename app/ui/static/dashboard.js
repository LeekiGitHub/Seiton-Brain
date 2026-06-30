(() => {
  function badge(status) {
    const cls =
      status === "failed" || status === "rejected"
        ? "err"
        : status === "appended"
          ? "warn"
          : "ok";
    return `<span class="badge ${cls}">${status}</span>`;
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
          <td class="truncate" title="${e.title}">${e.title}</td>
          <td>${e.category || "—"}</td>
          <td>${e.kind}</td>
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
          <td class="truncate" title="${n.title}">${n.title}</td>
          <td>${n.folder}</td>
          <td class="truncate" title="${n.vault_path}">${n.vault_path}</td>
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

  document.getElementById("btn-refresh").addEventListener("click", () => {
    load().catch((err) => alert(err.message));
  });

  load().catch((err) => {
    document.getElementById("entries-table-wrap").innerHTML =
      `<p class="empty">${err.message}</p>`;
  });
})();
