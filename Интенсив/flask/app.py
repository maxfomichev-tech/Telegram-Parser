"""Flask web application for displaying Telegram messages statistics."""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template

app = Flask(__name__)

# Путь к базе данных (на уровень выше от flask/)
DB_PATH = Path(__file__).parent.parent / "messages.db"


def init_db():
    """Инициализировать базу данных, создав таблицу, если её нет."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        conn.execute(
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
        conn.commit()
    finally:
        conn.close()


def get_db_connection():
    """Создать подключение к базе данных SQLite."""
    # Убеждаемся, что таблица существует
    init_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """Главная страница со статистикой."""
    conn = get_db_connection()
    
    try:
        # Всего сообщений
        total_count = conn.execute("SELECT COUNT(*) as count FROM messages").fetchone()["count"]
        
        # Проанализировано (все сообщения в базе считаются проанализированными)
        analyzed_count = total_count
        
        # Последняя выжимка (дата последнего сообщения)
        last_message = conn.execute(
            "SELECT date FROM messages ORDER BY date DESC LIMIT 1"
        ).fetchone()
        
        last_extraction = None
        if last_message:
            try:
                # Парсим ISO формат даты
                last_extraction = datetime.fromisoformat(last_message["date"])
            except (ValueError, TypeError):
                last_extraction = None
        
        stats = {
            "total_messages": total_count,
            "analyzed_messages": analyzed_count,
            "last_extraction": last_extraction,
        }
        
        return render_template("index.html", stats=stats)
    except sqlite3.OperationalError:
        # Если таблицы нет, возвращаем нулевую статистику
        stats = {
            "total_messages": 0,
            "analyzed_messages": 0,
            "last_extraction": None,
        }
        return render_template("index.html", stats=stats)
    finally:
        conn.close()


@app.route("/messages")
def messages():
    """Страница со списком всех сообщений."""
    conn = get_db_connection()
    
    try:
        # Получаем все сообщения, отсортированные по дате (новые сверху)
        messages_list = conn.execute(
            """
            SELECT id, chat_id, sender, text, date 
            FROM messages 
            ORDER BY date DESC
            """
        ).fetchall()
        
        # Преобразуем Row объекты в словари для удобства в шаблоне
        messages_data = []
        for msg in messages_list:
            try:
                date_obj = datetime.fromisoformat(msg["date"])
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_date = msg["date"] or "N/A"
            
            messages_data.append({
                "id": msg["id"],
                "chat_id": msg["chat_id"],
                "sender": msg["sender"],
                "text": msg["text"],
                "date": formatted_date,
            })
        
        return render_template("messages.html", messages=messages_data)
    except sqlite3.OperationalError:
        # Если таблицы нет, возвращаем пустой список
        return render_template("messages.html", messages=[])
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

