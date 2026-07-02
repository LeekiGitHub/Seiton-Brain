(() => {
  let selectedPath = null;
  let dirty = false;

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function formatDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("de-DE", {
      dateStyle: "short",
      timeStyle: "short",
    });
  }

  function setEditorEnabled(enabled) {
    document.getElementById("note-content").disabled = !enabled;
    document.getElementById("btn-save").disabled = !enabled;
    document.getElementById("btn-delete").disabled = !enabled;
  }

  function renderNotesList(items) {
    const wrap = document.getElementById("notes-list");
    if (!items.length) {
      wrap.innerHTML = '<p class="empty">Keine Notizen gefunden.</p>';
      return;
    }
    wrap.innerHTML = items
      .map(
        (n, idx) => `<button type="button" class="note-item${n.vault_path === selectedPath ? " active" : ""}" data-idx="${idx}">
          <span class="note-item-title">${escapeHtml(n.title)}</span>
          <span class="note-item-meta">${escapeHtml(n.folder)} · ${formatDate(n.mtime)}</span>
        </button>`
      )
      .join("");
    wrap.querySelectorAll(".note-item").forEach((btn) => {
      const idx = Number(btn.dataset.idx);
      const note = items[idx];
      btn.addEventListener("click", () => selectNote(note.vault_path, note.title));
    });
  }

  async function loadNotes() {
    const q = document.getElementById("filter-q").value.trim();
    const folder = document.getElementById("filter-folder").value;
    const params = new URLSearchParams({ limit: "100" });
    if (q) params.set("q", q);
    if (folder) params.set("folder", folder);

    const res = await fetch(`/api/ui/notes?${params}`);
    if (!res.ok) throw new Error("Notizen konnten nicht geladen werden");
    const data = await res.json();
    renderNotesList(data.items);
  }

  async function loadVaultConfig() {
    const res = await fetch("/api/ui/vault-config");
    if (!res.ok) throw new Error("Vault-Konfiguration konnte nicht geladen werden");
    const data = await res.json();
    const select = document.getElementById("filter-folder");
    const folders = [...new Set(Object.values(data.categories))].sort();
    folders.forEach((folder) => {
      const opt = document.createElement("option");
      opt.value = folder;
      opt.textContent = folder;
      select.appendChild(opt);
    });

    const rows = Object.entries(data.categories)
      .map(([cat, folder]) => `<tr><td>${escapeHtml(cat)}</td><td>${escapeHtml(folder)}</td></tr>`)
      .join("");
    document.getElementById("vault-config").innerHTML = `
      <p class="hit-path">Pfad: ${escapeHtml(data.vault_path)}</p>
      <table class="data"><thead><tr><th>Kategorie</th><th>Ordner</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  async function selectNote(path, titleHint) {
    if (dirty && !window.confirm("Ungespeicherte Änderungen verwerfen?")) {
      return;
    }
    selectedPath = path;
    dirty = false;
    document.getElementById("editor-title").textContent = titleHint || "Editor";
    document.getElementById("editor-path").textContent = path;
    document.getElementById("note-content").value = "Lade …";
    setEditorEnabled(false);

    const res = await fetch(`/api/ui/notes/content?${new URLSearchParams({ vault_path: path })}`);
    if (!res.ok) {
      document.getElementById("note-content").value = "";
      throw new Error("Notiz konnte nicht geladen werden");
    }
    const data = await res.json();
    if (data.title) {
      document.getElementById("editor-title").textContent = data.title;
    }
    document.getElementById("note-content").value = data.content;
    setEditorEnabled(true);
    await loadNotes();
  }

  document.getElementById("filter-form").addEventListener("submit", (e) => {
    e.preventDefault();
    loadNotes().catch((err) => alert(err.message));
  });

  document.getElementById("note-content").addEventListener("input", () => {
    dirty = true;
  });

  document.getElementById("btn-save").addEventListener("click", async () => {
    if (!selectedPath) return;
    try {
      const content = document.getElementById("note-content").value;
      const res = await fetch("/api/ui/notes/content", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vault_path: selectedPath, content }),
      });
      if (!res.ok) throw new Error("Speichern fehlgeschlagen");
      dirty = false;
      const data = await res.json();
      if (data.title) {
        document.getElementById("editor-title").textContent = data.title;
      }
      await loadNotes();
    } catch (err) {
      alert(err.message);
    }
  });

  document.getElementById("btn-delete").addEventListener("click", async () => {
    if (!selectedPath) return;
    if (!window.confirm(`Notiz wirklich löschen?\n\n${selectedPath}`)) return;
    try {
      const res = await fetch(`/api/ui/notes?${new URLSearchParams({ vault_path: selectedPath })}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Löschen fehlgeschlagen");
      selectedPath = null;
      dirty = false;
      document.getElementById("editor-title").textContent = "Editor";
      document.getElementById("editor-path").textContent = "";
      document.getElementById("note-content").value = "";
      setEditorEnabled(false);
      await loadNotes();
    } catch (err) {
      alert(err.message);
    }
  });

  Promise.all([loadVaultConfig(), loadNotes()]).catch((err) => {
    document.getElementById("notes-list").innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  });
})();
