"""Example Telethon client with SQLite persistence."""

import asyncio
import logging
from typing import List, Optional

from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl.custom import Dialog
from telethon.tl.custom.message import Message

import config
from db import Database, MessageRecord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("telethon-app")


async def list_dialogs(client: TelegramClient) -> List[Dialog]:
    """Fetch available dialogs (chats, channels, PMs)."""
    dialogs: List[Dialog] = []
    async for dialog in client.iter_dialogs():
        dialogs.append(dialog)
    return dialogs


async def fetch_recent_messages(
    client: TelegramClient, chat: Dialog, limit: int
) -> List[Message]:
    """Collect the latest N messages from the selected chat."""
    messages: List[Message] = []
    async for message in client.iter_messages(chat.id, limit=limit):
        messages.append(message)
    messages.reverse()  # oldest first
    return messages


def format_short_log(dialog: Dialog, message: Message) -> str:
    sender = message.sender_id or "unknown"
    text = (message.text or "").replace("\n", " ")
    return f"[{dialog.title}] {sender}: {text[:80]}"


async def save_message_to_db(db: Database, dialog: Dialog, message: Message) -> None:
    if message.id is None:
        return
    sender_display = str(message.sender_id or "unknown")
    text = message.message or ""
    record = MessageRecord(
        message_id=message.id,
        chat_id=dialog.id,
        sender=sender_display,
        text=text,
        date_iso=message.date.isoformat() if message.date else "",
    )
    inserted = await db.save_message(record)
    if inserted:
        logger.debug("Stored message %s from chat %s", record.message_id, dialog.id)


async def run_listener(client: TelegramClient, db: Database) -> None:
    """Attach a live listener for new messages."""

    @client.on(events.NewMessage)
    async def handler(event: events.NewMessage.Event) -> None:
        dialog = await event.get_chat()
        message = event.message
        await save_message_to_db(db, dialog, message)
        logger.info(format_short_log(dialog, message))

    logger.info("Listening for new messages...")
    await client.run_until_disconnected()


async def select_dialog(dialogs: List[Dialog]) -> Optional[Dialog]:
    """Ask the user to pick a dialog from a numbered list."""
    if not dialogs:
        logger.warning("No dialogs available.")
        return None

    print("Available dialogs:")
    for idx, dialog in enumerate(dialogs, start=1):
        print(f"{idx}. {dialog.title} (id={dialog.id})")

    choice_raw = input("Enter the number of a chat to fetch messages from: ").strip()
    if not choice_raw.isdigit():
        logger.error("Invalid choice.")
        return None

    choice = int(choice_raw)
    if 1 <= choice <= len(dialogs):
        return dialogs[choice - 1]

    logger.error("Choice out of range.")
    return None


async def main() -> None:
    db = Database()
    await db.connect()
    client = TelegramClient(config.session_name, config.api_id, config.api_hash)

    # Start client with interactive authorization if needed.
    await client.start()
    logger.info("Connected to Telegram.")

    dialogs = await list_dialogs(client)
    selected_dialog = await select_dialog(dialogs)
    if selected_dialog is None:
        await client.disconnect()
        await db.close()
        return

    try:
        logger.info("Fetching last 100 messages from '%s'...", selected_dialog.title)
        messages = await fetch_recent_messages(client, selected_dialog, limit=100)
        for msg in messages:
            await save_message_to_db(db, selected_dialog, msg)
        logger.info("Fetched and stored %d messages.", len(messages))
    except FloodWaitError as exc:
        logger.error("Rate limited by Telegram. Wait for %s seconds.", exc.seconds)
    except Exception:
        logger.exception("Failed to fetch messages.")

    # Start live listener with automatic reconnection handled by Telethon.
    try:
        await run_listener(client, db)
    finally:
        await client.disconnect()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

