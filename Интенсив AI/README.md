## CLI Summary Tool (OpenRouter)

Небольшой CLI-инструмент на Python, который делает краткую выжимку (summary) текста с помощью бесплатной модели на OpenRouter.

### Требования
- Python 3.10+
- `requests`
- `python-dotenv`

### Установка
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Создайте файл `.env` в корне проекта и добавьте ключ OpenRouter:
   ```env
   OPENROUTER_API_KEY=ваш_ключ
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
   ```
   Переменные `OPENROUTER_BASE_URL` и `OPENROUTER_MODEL` опциональны — указаны значения по умолчанию.

### Запуск
- С файла:
  ```bash
  python main.py summary --file messages.txt
  ```
- С текста:
  ```bash
  python main.py summary --text "любой текст"
  ```

При одновременном указании `--file` и `--text` используется `--text`. Если не указано ни то, ни другое — выводится ошибка и справка.

### Как это работает
- `main.py` — CLI-интерфейс, читает вход, вызывает `generate_summary`.
- `gigachat.py` — работа с OpenRouter API (адаптация требований под бесплатную модель).
- `utils.py` — вспомогательные функции и простое логирование.

### Пример вывода
```
> python main.py summary --text "Сегодня было солнечно, мы гуляли в парке..."
Краткая выжимка:
- Солнечная прогулка в парке прошла приятно.
```

### Возможные проблемы
- Отсутствует `OPENROUTER_API_KEY` — будет брошено исключение с подсказкой.
- Ошибка сети или API — сообщение с HTTP-кодом и телом ответа.



