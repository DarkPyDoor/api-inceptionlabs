# Библиотека api-inceptionlabs

Библиотека `api-inceptionlabs` — это неофициальная обёртка на Python для взаимодействия с API `https://chat.inceptionlabs.ai`. Она предоставляет удобный интерфейс для работы с чатом в стиле OpenAI, поддерживая как потоковый, так и не-потоковый режимы. Вы можете использовать её как API-сервер или напрямую как библиотеку в своих Python-скриптах.

**Отказ от ответственности**: Это неофициальный проект, созданный исключительно в образовательных целях. Он не предназначен для использования в продакшене. Автор не несёт ответственности за любые действия, совершённые с использованием этого кода, включая возможные нарушения условий сервиса `chat.inceptionlabs.ai`. Используйте на свой риск.

## Возможности

- **Генерация токенов авторизации**: Автоматическое создание учётных записей через Playwright с TTL токенов 6 часов.
- **Потоковый и не-потоковый режимы**: Поддержка `stream=True` для получения ответа по частям и `stream=False` для полного ответа.
- **Гибкость использования**: Работает как Flask API или как библиотека для прямого вызова.
- **Конфигурация через CLI**: Настройка порта, хоста, модели и количества аккаунтов через аргументы командной строки.

## Установка

Клонируйте репозиторий и установите библиотеку локально:

```bash
git clone https://github.com/DarkPyDoor/api-inceptionlabs.git
cd api-inceptionlabs
pip install .
```

### Зависимости
- `aiohttp` — для асинхронных HTTP-запросов.
- `playwright` — для генерации учётных записей (требуется установка браузеров: `playwright install`).
- `flask` — для запуска API (опционально).

## Использование как API

Вы можете запустить библиотеку как Flask-сервер, который принимает запросы в формате OpenAI.

### Запуск API
```bash
inceptionlabs-API --port 5001 --host 0.0.0.0 --model lambda.mercury-coder-small --min-accounts 2
```

- `--port`: Порт для сервера (по умолчанию 5001).
- `--host`: Хост (по умолчанию `0.0.0.0`).
- `--model`: Модель по умолчанию (по умолчанию `lambda.mercury-coder-small`).
- `--min-accounts`: Минимальное количество активных аккаунтов (по умолчанию 2).

API будет доступно по адресу: `http://0.0.0.0:5001/api/chat/completions`.

### Пример запроса (не-потоковый)
```bash
curl -X POST http://localhost:5001/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "lambda.mercury-coder-small", "messages": [{"role": "user", "content": "Привет!"}], "stream": false}'
```

**Ответ:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1741226494,
  "model": "lambda.mercury-coder-small",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Привет! У меня всё хорошо, спасибо за вопрос. Как у тебя дела? Чем могу помочь?"
      },
      "index": 0,
      "finish_reason": "stop"
    }
  ]
}
```

### Пример запроса (потоковый)
```bash
curl -X POST http://localhost:5001/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "lambda.mercury-coder-small", "messages": [{"role": "user", "content": "Привет!"}], "stream": true}'
```

**Ответ (поток):**
```
data: {"id": "chatcmpl-...", "choices": [{"delta": {"role": "assistant"}}]}
data: {"id": "chatcmpl-...", "choices": [{"delta": {"content": "Пр"}}]}
data: {"id": "chatcmpl-...", "choices": [{"delta": {"content": "ивет!"}}]}
...
data: [DONE]
```

## Использование как библиотеки

Библиотека позволяет напрямую вызывать методы для взаимодействия с `chat.inceptionlabs.ai` без запуска сервера.

### Пример не-потокового режима
Файл `non_stream.py`:
```python
import asyncio
import json
from api_inceptionlabs import AuthManager

async def main():
    auth = AuthManager()
    await auth.initialize_accounts()
    resp = await auth.complete_chat("lambda.mercury-coder-small", [{"role": "user", "content": "Привет!"}])
    print(json.loads(resp)["choices"][0]["message"]["content"])

asyncio.run(main())
```

**Запуск:**
```bash
python non_stream.py
```

**Вывод:**
```
Привет! У меня всё хорошо, спасибо за вопрос. Как у тебя дела? Чем могу помочь?
```

### Пример потокового режима
Файл `stream.py`:
```python
import asyncio
import json
from api_inceptionlabs import AuthManager

async def main():
    auth = AuthManager()
    await auth.initialize_accounts()
    async for chunk in auth.stream_chat("lambda.mercury-coder-small", [{"role": "user", "content": "Привет!"}]):
        if isinstance(chunk, dict) and "choices" in chunk:
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content", "") if isinstance(delta, dict) else delta
            if content:
                print(content, end="")
        else:
            print(f"Error chunk: {chunk}")

asyncio.run(main())
```

**Запуск:**
```bash
python stream.py
```

**Вывод:**
```
Привет! У меня всё хорошо, спасибо за вопрос. Как у тебя дела? Чем могу помочь?
```

## Особенности

- **Автоматическая генерация аккаунтов**: Если файл `accounts.json` пуст или отсутствует, библиотека использует Playwright для создания новых учётных записей (около 20 секунд на аккаунт).
- **Управление токенами**: Токены имеют TTL 6 часов (настраивается в `config.py` через `TOKEN_TTL`). Истёкшие токены автоматически удаляются.
- **Фоновая инициализация**: При запуске API или библиотеки аккаунты генерируются в фоновом режиме, не блокируя основной процесс.
- **Обработка ошибок**: Ошибки API (например, 400, 401) возвращаются как строки, что требует проверки типа данных в потоковом режиме.
- **Конфигурация**: Параметры, такие как `MIN_ACCOUNTS` (минимальное количество аккаунтов), `TOKEN_TTL` и `PRE_EXPIRY_THRESHOLD`, настраиваются через `config.py` или CLI при запуске API.

## Поддерживаемые модели
- `lambda.mercury-coder-small` — основная модель, протестированная в проекте.
- Другие модели могут поддерживаться сервером `chat.inceptionlabs.ai`, но требуют проверки (см. документацию API, если доступна).

## Конечная точка API
Все запросы отправляются на: `https://chat.inceptionlabs.ai/api/chat/completions`.

## Зависимости
- `Python 3.10+`
- `aiohttp` — для асинхронных запросов.
- `playwright` — для генерации учётных записей (установите браузеры с помощью `playwright install`).
- `flask` — для API-режима.
- `requests` — для дополнительных утилит.

## Установка Playwright
После установки пакета выполните:
```bash
playwright install
```
Это установит необходимые браузеры (Chromium) для генерации аккаунтов.

## Примечания
- **Генерация аккаунтов**: Если Playwright не может создать аккаунт (например, из-за CAPTCHA или блокировки), используйте заранее подготовленный `accounts.json`.
- **Ошибки соединения**: При нестабильном подключении к `chat.inceptionlabs.ai` возможны ошибки вроде `Connection closed`. Увеличьте `timeout` в `auth_manager.py` (например, до 120 секунд), если это происходит часто.
- **Отладка**: Включите вывод отладки в консоль, добавив `print` в нужных местах `auth_manager.py` для диагностики.

## Пример `accounts.json`
Если вы хотите избежать генерации аккаунтов, создайте файл `accounts.json` в директории библиотеки:
```json
{
  "active": [
    {
      "bearer": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "cookies": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
      "created_at": 1741226475
    }
  ],
  "rate_limited": []
}
```

## Правовые аспекты
Этот проект предоставляется "как есть" для образовательных целей. Автор не несёт ответственности за последствия его использования, включая ограничения скорости API, блокировки аккаунтов или юридические проблемы. Уважайте условия обслуживания `https://chat.inceptionlabs.ai` и используйте библиотеку ответственно.

---

**[English](README.md) | [Русский](README_ru.md)**

---
