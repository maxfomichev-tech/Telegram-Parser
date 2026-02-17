"""Telegram бот для суммаризации сообщений из базы данных."""

import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
import telebot

from database import Database

# Загрузка переменных окружения
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
db = Database()


def summarize_text(text: str) -> str:
    """Суммаризировать текст через OpenRouter, максимум 5 предложений.
    
    Args:
        text: Текст для суммаризации
        
    Returns:
        Суммаризированный текст (максимум 5 предложений)
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_REFERRER", "https://t.me"),
        "X-Title": os.getenv("OPENROUTER_TITLE", "TelegramBot"),
    }
    
    # Инструкция для суммаризации с ограничением в 5 предложений
    system_prompt = (
        "Ты помощник для создания кратких выжимок текста. "
        "Создай краткую суммаризацию текста, выделяя самое главное. "
        "Ответ должен содержать максимум 5 предложений. "
        "Будь точным и лаконичным."
    )
    
    user_prompt = f"Суммаризируй следующий текст (максимум 5 предложений):\n\n{text}"
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code == 429:
            return "Ошибка: превышен лимит запросов. Подожди немного и попробуй снова."
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError(f"OpenRouter вернул пустой ответ: {data}")
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError(f"OpenRouter вернул пустой ответ: {data}")
        return content
    except Exception as exc:
        logger.exception("Ошибка при запросе к OpenRouter")
        return f"Ошибка при суммаризации: {exc}"


@bot.message_handler(commands=["start", "help"])
def send_welcome(message: telebot.types.Message) -> None:
    """Обработчик команд /start и /help."""
    help_text = (
        "Привет! Я бот для суммаризации сообщений.\n\n"
        "Я сохраняю все входящие текстовые сообщения в базу данных.\n\n"
        "Команды:\n"
        "/summarize - создать суммаризацию всех новых сообщений (максимум 5 предложений)\n"
        "/stats - показать статистику сообщений\n"
        "/help - показать это сообщение"
    )
    bot.reply_to(message, help_text)


@bot.message_handler(commands=["stats"])
def show_stats(message: telebot.types.Message) -> None:
    """Показать статистику по сообщениям в БД."""
    try:
        total = db.get_message_count(processed=None)
        processed = db.get_message_count(processed=True)
        unprocessed = db.get_message_count(processed=False)
        
        stats_text = (
            f"📊 Статистика сообщений:\n\n"
            f"Всего сообщений: {total}\n"
            f"Обработано: {processed}\n"
            f"Новых (необработанных): {unprocessed}"
        )
        bot.reply_to(message, stats_text)
    except Exception as exc:
        logger.exception("Ошибка при получении статистики")
        bot.reply_to(message, f"Ошибка при получении статистики: {exc}")


@bot.message_handler(commands=["summarize"])
def handle_summarize(message: telebot.types.Message) -> None:
    """Создать суммаризацию всех новых (необработанных) сообщений."""
    try:
        # Получаем все необработанные сообщения
        unprocessed = db.get_unprocessed_messages()
        
        if not unprocessed:
            bot.reply_to(message, "Нет новых сообщений для суммаризации.")
            return
        
        # Уведомляем пользователя о начале обработки
        bot.send_chat_action(message.chat.id, "typing")
        processing_msg = bot.reply_to(
            message, 
            f"Обрабатываю {len(unprocessed)} новых сообщений..."
        )
        
        # Объединяем все тексты сообщений
        texts = []
        message_ids = []
        for msg_id, sender, text in unprocessed:
            message_ids.append(msg_id)
            if text.strip():  # Игнорируем пустые сообщения
                texts.append(f"[{sender}]: {text}")
        
        if not texts:
            bot.edit_message_text(
                "Все новые сообщения пустые, нечего суммаризировать.",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id
            )
            return
        
        # Объединяем все тексты
        combined_text = "\n\n".join(texts)
        
        # Если текст слишком длинный, обрезаем его (лимит для API)
        max_length = 50000  # Примерный лимит
        if len(combined_text) > max_length:
            combined_text = combined_text[:max_length] + "\n\n[...текст обрезан...]"
        
        # Выполняем суммаризацию
        summary = summarize_text(combined_text)
        
        # Помечаем сообщения как обработанные
        db.mark_messages_as_processed(message_ids)
        
        # Отправляем результат
        result_text = f"📝 *Суммаризация* (обработано сообщений: {len(message_ids)}):\n\n{summary}"
        bot.edit_message_text(
            result_text,
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            parse_mode="Markdown"
        )
        
        logger.info(
            "Суммаризация завершена. Обработано сообщений: %d", 
            len(message_ids)
        )
        
    except Exception as exc:
        logger.exception("Ошибка при суммаризации")
        bot.reply_to(message, f"Ошибка при создании суммаризации: {exc}")


@bot.message_handler(func=lambda msg: True, content_types=["text"])
def handle_text(message: telebot.types.Message) -> None:
    """Обработчик всех текстовых сообщений - сохраняет их в БД."""
    try:
        # Сохраняем сообщение в БД
        sender_name = (
            f"{message.from_user.first_name or ''} "
            f"{message.from_user.last_name or ''}".strip()
        )
        if not sender_name:
            sender_name = f"user_{message.from_user.id}"
        
        date_str = datetime.fromtimestamp(message.date).isoformat()
        
        saved = db.save_message(
            message_id=message.message_id,
            chat_id=message.chat.id,
            sender=sender_name,
            text=message.text or "",
            date=date_str
        )
        
        if saved:
            logger.info(
                "Сохранено новое сообщение ID=%d от %s в чат %d",
                message.message_id,
                sender_name,
                message.chat.id
            )
            # Можно отправить подтверждение (опционально)
            # bot.reply_to(message, "✓ Сообщение сохранено")
        else:
            logger.debug(
                "Сообщение ID=%d уже существует в БД",
                message.message_id
            )
            
    except Exception as exc:
        logger.exception("Ошибка при сохранении сообщения в БД")
        # Не отправляем ошибку пользователю, чтобы не спамить


if __name__ == "__main__":
    logger.info("Бот запущен")
    logger.info("База данных: %s", db.db_path)
    bot.infinity_polling()
