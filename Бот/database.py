"""Синхронный модуль для работы с базой данных сообщений."""

import sqlite3
import os
from typing import List, Tuple, Optional
from pathlib import Path


class Database:
    """Синхронный wrapper для работы с SQLite БД сообщений."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Инициализация БД.
        
        Args:
            db_path: Путь к БД. По умолчанию используется БД из папки Интенсив.
        """
        if db_path is None:
            # Путь к БД в папке Интенсив
            db_path = r"C:\Users\maxfo\OneDrive\Рабочий стол\Интенсив\messages.db"
        self.db_path = db_path
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Убедиться, что схема БД актуальна (добавить поле processed если нужно)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Проверяем, существует ли поле processed
            cursor.execute("PRAGMA table_info(messages)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if "processed" not in columns:
                # Добавляем поле processed
                cursor.execute("ALTER TABLE messages ADD COLUMN processed INTEGER DEFAULT 0")
                conn.commit()
                print("Добавлено поле 'processed' в таблицу messages")
        finally:
            conn.close()

    def save_message(
        self, message_id: int, chat_id: int, sender: str, text: str, date: str
    ) -> bool:
        """Сохранить сообщение в БД.
        
        Returns:
            True если сообщение было добавлено, False если уже существует.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Проверяем, существует ли сообщение
            cursor.execute("SELECT 1 FROM messages WHERE id = ? LIMIT 1", (message_id,))
            if cursor.fetchone():
                return False  # Сообщение уже существует

            # Вставляем новое сообщение (processed = 0 по умолчанию)
            cursor.execute(
                """
                INSERT INTO messages (id, chat_id, sender, text, date, processed)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (message_id, chat_id, sender, text, date),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def get_unprocessed_messages(self) -> List[Tuple[int, str, str]]:
        """Получить все необработанные сообщения.
        
        Returns:
            Список кортежей (id, sender, text) необработанных сообщений.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, sender, text 
                FROM messages 
                WHERE processed = 0 
                ORDER BY id ASC
                """
            )
            return [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        finally:
            conn.close()

    def mark_messages_as_processed(self, message_ids: List[int]) -> None:
        """Пометить сообщения как обработанные.
        
        Args:
            message_ids: Список ID сообщений для пометки.
        """
        if not message_ids:
            return
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(message_ids))
            cursor.execute(
                f"UPDATE messages SET processed = 1 WHERE id IN ({placeholders})",
                message_ids,
            )
            conn.commit()
        finally:
            conn.close()

    def get_message_count(self, processed: Optional[bool] = None) -> int:
        """Получить количество сообщений.
        
        Args:
            processed: Если None - все сообщения, True - обработанные, False - необработанные.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if processed is None:
                cursor.execute("SELECT COUNT(*) FROM messages")
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE processed = ?",
                    (1 if processed else 0,),
                )
            return cursor.fetchone()[0]
        finally:
            conn.close()

