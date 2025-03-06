# api-inceptionlabs Library

The `api-inceptionlabs` library is an unofficial Python wrapper for interacting with the `https://chat.inceptionlabs.ai` API. It provides a convenient OpenAI-style interface for chat completions, supporting both streaming and non-streaming modes. You can use it as a Flask API server or directly as a library in your Python scripts.

**Disclaimer**: This is an unofficial project created solely for educational purposes. It is not intended for production use. The author is not responsible for any actions taken using this code, including potential violations of the `chat.inceptionlabs.ai` terms of service. Use at your own risk.

## Features

- **Token Authorization Generation**: Automatically creates accounts via Playwright with a token TTL of 6 hours.
- **Streaming and Non-Streaming Modes**: Supports `stream=True` for partial responses and `stream=False` for full responses.
- **Flexible Usage**: Can be run as a Flask API or called directly as a library.
- **CLI Configuration**: Customize port, host, model, and account count via command-line arguments.

## Installation

Clone the repository and install the library locally:

```bash
git clone https://github.com/DarkPyDoor/api-inceptionlabs.git
cd api-inceptionlabs
pip install .
```

### Dependencies
- `aiohttp` — for asynchronous HTTP requests.
- `playwright` — for account generation (requires browser installation: `playwright install`).
- `flask` — for running the API (optional).

## Usage as an API

You can run the library as a Flask server that accepts OpenAI-style requests.

### Running the API
```bash
inceptionlabs-API --port 5001 --host 0.0.0.0 --model lambda.mercury-coder-small --min-accounts 2
```

- `--port`: Server port (default: 5001).
- `--host`: Host address (default: `0.0.0.0`).
- `--model`: Default model (default: `lambda.mercury-coder-small`).
- `--min-accounts`: Minimum number of active accounts (default: 2).

The API will be available at: `http://0.0.0.0:5001/api/chat/completions`.

### Example Request (Non-Streaming)
```bash
curl -X POST http://localhost:5001/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "lambda.mercury-coder-small", "messages": [{"role": "user", "content": "Hello!"}], "stream": false}'
```

**Response:**
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
        "content": "Hello! I'm doing great, thanks for asking. How are you? How can I assist you?"
      },
      "index": 0,
      "finish_reason": "stop"
    }
  ]
}
```

### Example Request (Streaming)
```bash
curl -X POST http://localhost:5001/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "lambda.mercury-coder-small", "messages": [{"role": "user", "content": "Hello!"}], "stream": true}'
```

**Response (Stream):**
```
data: {"id": "chatcmpl-...", "choices": [{"delta": {"role": "assistant"}}]}
data: {"id": "chatcmpl-...", "choices": [{"delta": {"content": "He"}}]}
data: {"id": "chatcmpl-...", "choices": [{"delta": {"content": "llo!"}}]}
...
data: [DONE]
```

## Usage as a Library

The library allows direct method calls to interact with `chat.inceptionlabs.ai` without running a server.

### Example (Non-Streaming Mode)
File `non_stream.py`:
```python
import asyncio
import json
from api_inceptionlabs import AuthManager

async def main():
    auth = AuthManager()
    await auth.initialize_accounts()
    resp = await auth.complete_chat("lambda.mercury-coder-small", [{"role": "user", "content": "Hello!"}])
    print(json.loads(resp)["choices"][0]["message"]["content"])

asyncio.run(main())
```

**Run:**
```bash
python non_stream.py
```

**Output:**
```
Hello! I'm doing great, thanks for asking. How are you? How can I assist you?
```

### Example (Streaming Mode)
File `stream.py`:
```python
import asyncio
import json
from api_inceptionlabs import AuthManager

async def main():
    auth = AuthManager()
    await auth.initialize_accounts()
    async for chunk in auth.stream_chat("lambda.mercury-coder-small", [{"role": "user", "content": "Hello!"}]):
        if isinstance(chunk, dict) and "choices" in chunk:
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content", "") if isinstance(delta, dict) else delta
            if content:
                print(content, end="")
        else:
            print(f"Error chunk: {chunk}")

asyncio.run(main())
```

**Run:**
```bash
python stream.py
```

**Output:**
```
Hello! I'm doing great, thanks for asking. How are you? How can I assist you?
```

## Features

- **Automatic Account Generation**: If `accounts.json` is empty or missing, the library uses Playwright to create new accounts (about 20 seconds per account).
- **Token Management**: Tokens have a TTL of 6 hours (configurable in `config.py` via `TOKEN_TTL`). Expired tokens are automatically removed.
- **Background Initialization**: Accounts are generated in the background when running as an API or library, avoiding blocking the main process.
- **Error Handling**: API errors (e.g., 400, 401) are returned as strings, requiring type checking in streaming mode.
- **Configuration**: Parameters like `MIN_ACCOUNTS`, `TOKEN_TTL`, and `PRE_EXPIRY_THRESHOLD` can be adjusted in `config.py` or via CLI when running the API.

## Supported Models
- `lambda.mercury-coder-small` — the primary model tested in this project.
- Other models may be supported by `chat.inceptionlabs.ai`, but require verification (consult the API documentation if available).

## API Endpoint
All requests are sent to: `https://chat.inceptionlabs.ai/api/chat/completions`.

## Dependencies
- `Python 3.10+`
- `aiohttp` — for asynchronous requests.
- `playwright` — for account generation (install browsers with `playwright install`).
- `flask` — for API mode.
- `requests` — for additional utilities.

## Playwright Installation
After installing the package, run:
```bash
playwright install
```
This installs the required browsers (Chromium) for account generation.

## Notes
- **Account Generation**: If Playwright fails to create an account (e.g., due to CAPTCHA or blocking), use a pre-prepared `accounts.json`.
- **Connection Errors**: Unstable connections to `chat.inceptionlabs.ai` may cause `Connection closed` errors. Increase the `timeout` in `auth_manager.py` (e.g., to 120 seconds) if this occurs frequently.
- **Debugging**: Enable console debug output by adding `print` statements in `auth_manager.py` for troubleshooting.

## Example `accounts.json`
To skip account generation, create an `accounts.json` file in the library directory:
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

## Legal Considerations
This project is provided "as is" for educational purposes. The author is not liable for any consequences of its use, including API rate limits, account bans, or legal issues. Respect the terms of service of `https://chat.inceptionlabs.ai` and use the library responsibly.

---

**[English](README.md) | [Русский](README_ru.md)**

---

If you like my project or what I do, please consider buying me sweets via Binance Pay: **ID 438 485 773** 🍬
