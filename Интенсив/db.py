"""SQLite helpers for storing Telegram messages asynchronously."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import aiosqlite


@dataclass
class MessageRecord:
    """Container for a message to be stored in the database."""

    message_id: int
    chat_id: int
    sender: str
    text: str
    date_iso: str


class Database:
    """Async wrapper around SQLite to store messages."""

    def __init__(self, path: str = "messages.db") -> None:
        self.path = path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Open a connection and ensure schema exists."""
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._create_schema()

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _create_schema(self) -> None:
        assert self._conn is not None
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                date TEXT NOT NULL
            );
            """
        )
        await self._conn.commit()

    async def save_message(self, record: MessageRecord) -> bool:
        """Persist a message if it is not already stored.

        Returns True if inserted, False if duplicate.
        """
        assert self._conn is not None
        async with self._lock:
            cursor = await self._conn.execute(
                "SELECT 1 FROM messages WHERE id = ? LIMIT 1;",
                (record.message_id,),
            )
            row = await cursor.fetchone()
            await cursor.close()
            if row:
                return False

            await self._conn.execute(
                """
                INSERT INTO messages (id, chat_id, sender, text, date)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    record.message_id,
                    record.chat_id,
                    record.sender,
                    record.text,
                    record.date_iso,
                ),
            )
            await self._conn.commit()
            return True

