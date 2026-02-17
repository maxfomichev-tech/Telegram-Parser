"""Configuration for Telegram client credentials and session."""

# Replace with your own values from https://my.telegram.org
api_id: int = 38618129  # type: ignore[assignment]
api_hash: str = "751e6d5838472c3278aca9a0a81a3a16"

# Session file name; Telethon will create/refresh this file locally
session_name: str = "telethon_session"

