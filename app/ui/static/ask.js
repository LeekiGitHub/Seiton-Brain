(() => {
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function renderSearchHits(items, query) {
    const wrap = document.getElementById("search-results");
    if (!items.length) {
      wrap.innerHTML = `<p class="empty">Keine Treffer für „${escapeHtml(query)}".</p>`;
      return;
    }
    const rows = items
      .map(
        (hit) => `<article class="hit">
          <h3 class="hit-title">${escapeHtml(hit.title)}</h3>
          <p class="hit-meta">${escapeHtml(hit.folder)} · ${escapeHtml(hit.category)}</p>
          <p class="hit-snippet">${escapeHtml(hit.snippet)}</p>
          <p class="hit-path">${escapeHtml(hit.vault_path)}</p>
        </article>`
      )
      .join("");
    wrap.innerHTML = rows;
  }

  function appendChatMessage(role, html) {
    const log = document.getElementById("chat-log");
    const msg = document.createElement("div");
    msg.className = `chat-msg ${role}`;
    msg.innerHTML = html;
    log.appendChild(msg);
    log.scrollTop = log.scrollHeight;
  }

  function renderSources(sources, confidence) {
    if (!sources.length) {
      return confidence > 0
        ? `<p class="chat-meta">Konfidenz: ${Math.round(confidence * 100)}%</p>`
        : "";
    }
    const links = sources
      .map((s) => `<li>${escapeHtml(s.title)}${s.vault_path ? ` <span class="hit-path">(${escapeHtml(s.vault_path)})</span>` : ""}</li>`)
      .join("");
    return `<p class="chat-meta">Konfidenz: ${Math.round(confidence * 100)}%</p><p class="chat-sources-label">Quellen:</p><ul class="chat-sources">${links}</ul>`;
  }

  document.getElementById("search-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = document.getElementById("search-query").value.trim();
    if (!q) return;

    const wrap = document.getElementById("search-results");
    wrap.innerHTML = '<p class="empty">Suche …</p>';

    const semanticEl = document.getElementById("search-semantic");
    const params = new URLSearchParams({ q, limit: "15" });
    if (semanticEl) {
      params.set("semantic", semanticEl.checked ? "true" : "false");
    }

    try {
      const res = await fetch(`/api/ui/search?${params}`);
      if (!res.ok) throw new Error("Suche fehlgeschlagen");
      const data = await res.json();
      renderSearchHits(data.items, data.query);
    } catch (err) {
      wrap.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
    }
  });

  document.getElementById("ask-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("ask-question");
    const btn = document.getElementById("ask-submit");
    const question = input.value.trim();
    if (!question) return;

    appendChatMessage("user", `<p>${escapeHtml(question)}</p>`);
    input.value = "";
    btn.disabled = true;

    const pending = document.createElement("div");
    pending.className = "chat-msg assistant pending";
    pending.textContent = "Ich durchsuche dein Brain …";
    document.getElementById("chat-log").appendChild(pending);

    try {
      const res = await fetch("/api/ui/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      pending.remove();
      if (!res.ok) throw new Error("Antwort konnte nicht geladen werden");
      const data = await res.json();
      appendChatMessage(
        "assistant",
        `<p>${escapeHtml(data.answer)}</p>${renderSources(data.sources, data.confidence)}`
      );
    } catch (err) {
      pending.remove();
      appendChatMessage("assistant", `<p class="chat-error">${escapeHtml(err.message)}</p>`);
    } finally {
      btn.disabled = false;
      input.focus();
    }
  });
})();
