# Telethon Async Message Collector

Небольшой пример бота/клиента на Telethon с сохранением сообщений в SQLite.

## Структура
- `main.py` — запуск клиента, выбор чата, сбор последних N сообщений, live‑слушатель новых.
- `db.py` — асинхронная работа с SQLite, таблица `messages`, проверка дубликатов по `id`.
- `config.py` — ваши `api_id`, `api_hash`, `session_name`.
- `requirements.txt` — зависимости (`telethon`, `aiosqlite`).

## Подготовка
1) Получите креды на https://my.telegram.org и заполните в `config.py`:
   ```python
   api_id = 123456
   api_hash = "your_api_hash_here"
   session_name = "telethon_session"
   ```
2) Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Запуск
```bash
python main.py
```
- При первом запуске Telethon запросит код/пароль Telegram.
- Скрипт покажет список ваших диалогов. Введите номер чата — он соберёт последние 100 сообщений, сохранит их в `messages.db`, затем запустит live‑слушатель.
- Новые сообщения логируются в консоль в формате: `[CHAT TITLE] sender: text`.

## База данных
- SQLite файл: `messages.db`.
- Таблица `messages(id, chat_id, sender, text, date)`.
- Перед вставкой проверяется дубликат по `id`.

## Полезно знать
- Telethon сам пытается переподключаться; `FloodWaitError` логируется.
- `session_name` можно сменить, чтобы иметь отдельные сессии.
- Для сбора другого количества сообщений поменяйте `limit` в вызове `fetch_recent_messages` внутри `main.py`.


