"""Slash-Commands fuer den Telegram-Bot.

Wir halten die Handler bewusst klein und stringbasiert: jeder Handler
liefert einen Antwort-Text zurueck, den der Webhook an Telegram schickt.
Keine Inline-Keyboards, keine Callback-Queries — das halten wir uns fuer
spaeter auf, wenn der Bedarf konkret wird.

DB-Lookups sind in dedizierten ``_query_*``-Funktionen gekapselt, damit
sie in Tests einzeln gemockt werden koennen.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entry import Entry
from app.vault.writer import delete_note

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "Verfügbare Commands:\n"
    "/help — diese Hilfe\n"
    "/recent [n] — letzte N Notizen (max 20, Default 5)\n"
    "/find <begriff> — sucht Notizen nach Titel\n"
    "/undo — zeigt deine letzte Notiz; /undo confirm löscht sie\n"
    "\n"
    "Sonst: Text- oder Sprachnachricht senden — wird klassifiziert und in "
    "deinem Vault gespeichert."
)

DEFAULT_RECENT_LIMIT = 5
MAX_RECENT_LIMIT = 20
MAX_FIND_RESULTS = 10


async def _query_recent(
    db: AsyncSession, chat_id: int, limit: int
) -> list[Entry]:
    stmt = (
        select(Entry)
        .where(Entry.telegram_chat_id == chat_id)
        .order_by(Entry.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def _query_find(
    db: AsyncSession, chat_id: int, query: str, limit: int
) -> list[Entry]:
    # Postgres ILIKE — case-insensitive Substring-Match. Wenn wir spaeter
    # mal pg_trgm oder pgvector (E17) dranbauen, lebt der Code hier.
    stmt = (
        select(Entry)
        .where(Entry.telegram_chat_id == chat_id)
        .where(Entry.title.ilike(f"%{query}%"))
        .order_by(Entry.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def _query_latest(
    db: AsyncSession, chat_id: int
) -> Entry | None:
    stmt = (
        select(Entry)
        .where(Entry.telegram_chat_id == chat_id)
        .order_by(Entry.created_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _delete_entry(db: AsyncSession, entry: Entry) -> None:
    await db.delete(entry)
    await db.commit()


def _format_entry_line(entry: Entry) -> str:
    return f"• [[{entry.title}]]"


def _parse_int_arg(arg: str, default: int, maximum: int) -> int:
    if not arg:
        return default
    try:
        n = int(arg)
    except ValueError:
        return default
    return max(1, min(n, maximum))


async def _cmd_help() -> str:
    return HELP_TEXT


async def _cmd_recent(db: AsyncSession, chat_id: int, args: str) -> str:
    limit = _parse_int_arg(args.strip(), DEFAULT_RECENT_LIMIT, MAX_RECENT_LIMIT)
    entries = await _query_recent(db, chat_id, limit)
    if not entries:
        return "Noch keine Notizen — schick einfach eine Text- oder Sprachnachricht."
    lines = [f"Deine letzten {len(entries)} Notizen:"]
    lines.extend(_format_entry_line(e) for e in entries)
    return "\n".join(lines)


async def _cmd_find(db: AsyncSession, chat_id: int, args: str) -> str:
    query = args.strip()
    if not query:
        return "Nutzung: /find <begriff> — sucht in deinen Notiz-Titeln."
    entries = await _query_find(db, chat_id, query, MAX_FIND_RESULTS)
    if not entries:
        return f'Keine Notiz gefunden für „{query}“.'
    lines = [f'Treffer für „{query}“ ({len(entries)}):']
    lines.extend(_format_entry_line(e) for e in entries)
    return "\n".join(lines)


async def _cmd_undo(db: AsyncSession, chat_id: int, args: str) -> str:
    confirm = args.strip().lower() == "confirm"
    latest = await _query_latest(db, chat_id)
    if latest is None:
        return "Nichts zum Rückgängig-Machen."

    if not confirm:
        kind_hint = ""
        if latest.status == "appended":
            kind_hint = (
                "\n\nHinweis: Das war ein Update einer bestehenden Notiz. "
                "/undo confirm entfernt nur den DB-Eintrag — den Update-Block "
                "in der Notiz selbst musst du in Obsidian manuell löschen."
            )
        return (
            f"Letzte Notiz: [[{latest.title}]] ({latest.status})\n"
            f"Datei: {latest.vault_path or '—'}\n"
            f"\n"
            f"Sende /undo confirm um sie zu löschen.{kind_hint}"
        )

    title = latest.title
    vault_path = latest.vault_path
    status = latest.status

    file_was_deleted = False
    if status != "appended" and vault_path:
        try:
            file_was_deleted = delete_note(vault_path)
        except OSError as exc:
            logger.warning("Failed to delete vault file %r: %s", vault_path, exc)

    await _delete_entry(db, latest)

    if status == "appended":
        return (
            f"DB-Eintrag für [[{title}]] gelöscht. "
            f"Den Update-Block in der Notiz bitte manuell in Obsidian entfernen."
        )
    if file_was_deleted:
        return f"Gelöscht: [[{title}]] (DB + Vault-Datei)."
    return (
        f"DB-Eintrag für [[{title}]] gelöscht. "
        f"Vault-Datei war nicht (mehr) vorhanden."
    )


async def handle_command(
    text: str, chat_id: int, db: AsyncSession
) -> str | None:
    """Dispatched Slash-Commands. Liefert ``None``, wenn der Text gar
    kein Command ist (z. B. normale Capture-Nachricht).
    """
    if not text.startswith("/"):
        return None

    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # Telegram-Convention: ``/cmd@BotName`` -> strip Bot-Suffix.
    if "@" in cmd:
        cmd = cmd.split("@", 1)[0]

    if cmd in ("/start", "/help"):
        return await _cmd_help()
    if cmd == "/recent":
        return await _cmd_recent(db, chat_id, args)
    if cmd == "/find":
        return await _cmd_find(db, chat_id, args)
    if cmd == "/undo":
        return await _cmd_undo(db, chat_id, args)

    return f"Unbekannter Command: {cmd}\n\n{HELP_TEXT}"
