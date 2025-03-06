import asyncio
import os
import json
import time
import random
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from .playwright_auth import get_new_credentials
from .config import TOKEN_TTL, MIN_ACCOUNTS, PRE_EXPIRY_THRESHOLD, MAX_WORKERS

class AuthManager:
    def __init__(self):
        self.api_host = "https://chat.inceptionlabs.ai"
        self.accounts_file = os.path.join(os.path.dirname(__file__), 'accounts.json')
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.accounts = {"active": [], "rate_limited": []}  # Инициализация по умолчанию
        self.active_account = None
        self.load_accounts()  # Синхронная загрузка
        if self.accounts["active"]:
            self.active_account = random.choice(self.accounts["active"])

    def load_accounts(self):
        default_accounts = {"active": [], "rate_limited": []}
        if not os.path.exists(self.accounts_file):
            self.accounts = default_accounts
            self.save_accounts()
        else:
            try:
                with open(self.accounts_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        self.accounts = default_accounts
                    else:
                        self.accounts = json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                self.accounts = default_accounts
            self.save_accounts()
        self._cleanup_expired_accounts()

    def save_accounts(self):
        with open(self.accounts_file, 'w') as f:
            json.dump(self.accounts, f, indent=2)

    def _cleanup_expired_accounts(self):
        current_time = time.time()
        self.accounts["active"] = [
            acc for acc in self.accounts["active"]
            if acc.get("created_at", 0) + TOKEN_TTL > current_time
        ]
        self.accounts["rate_limited"] = [
            acc for acc in self.accounts["rate_limited"]
            if acc.get("created_at", 0) + TOKEN_TTL > current_time
        ]
        self.save_accounts()

    async def _generate_account(self):
        try:
            creds = await get_new_credentials()
            if creds:
                creds["created_at"] = time.time()
                return creds
        except Exception as e:
            return None

    async def _generate_multiple_accounts(self, count):
        tasks = [self._generate_account() for _ in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        new_accounts = [r for r in results if r and not isinstance(r, Exception)]
        if not new_accounts and not self.accounts["active"]:
            print(f"Failed to generate {count} accounts")
        self.accounts["active"].extend(new_accounts)
        self.save_accounts()

    async def _maintain_accounts(self):
        while True:
            self._cleanup_expired_accounts()
            current_time = time.time()
            active_count = len(self.accounts["active"])
            near_expiry = sum(1 for acc in self.accounts["active"]
                              if acc.get("created_at", 0) + TOKEN_TTL - current_time < PRE_EXPIRY_THRESHOLD)
            if active_count + near_expiry < MIN_ACCOUNTS:
                needed = MIN_ACCOUNTS - (active_count - near_expiry)
                await self._generate_multiple_accounts(needed)
            await asyncio.sleep(60)

    async def initialize_accounts(self):
        if not self.accounts["active"]:
            await self._generate_multiple_accounts(MIN_ACCOUNTS)
        if self.accounts["active"]:
            self.active_account = random.choice(self.accounts["active"])
        else:
            raise ValueError("No active accounts available after initialization")

    async def get_active_account(self):
        self._cleanup_expired_accounts()
        if not self.accounts.get("active"):
            await self._generate_multiple_accounts(MIN_ACCOUNTS)
        self.active_account = random.choice(self.accounts["active"])
        return self.active_account

    def mark_rate_limited(self, account):
        if not account:
            return
        if account in self.accounts["active"]:
            self.accounts["active"].remove(account)
        self.save_accounts()

    async def get_headers(self):
        if not self.active_account:
            self.active_account = await self.get_active_account()
        bearer = self.active_account.get("bearer")
        cookies = self.active_account.get("cookies", {})
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer}",
            "Cookie": cookie_string,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def stream_chat(self, model, messages):
        url = f"{self.api_host}/api/chat/completions"
        headers = await self.get_headers()
        data = {"model": model, "messages": messages, "stream": True}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=data, timeout=60) as response:
                    if response.status == 401:
                        self.mark_rate_limited(self.active_account)
                        self.active_account = await self.get_active_account()
                        headers = await self.get_headers()
                        async with session.post(url, headers=headers, json=data, timeout=60) as retry_response:
                            if retry_response.status != 200:
                                error_text = await retry_response.text()
                                yield {"choices": [{"delta": f"API error: {retry_response.status} - {error_text[:200]}"}]}
                            else:
                                async for line in retry_response.content:
                                    line = line.decode('utf-8', errors='replace').strip()
                                    if line.startswith('data: '):
                                        if line == 'data: [DONE]':
                                            break
                                        try:
                                            json_str = line[6:]
                                            chunk = json.loads(json_str)
                                            yield chunk
                                        except json.JSONDecodeError as e:
                                            yield {"choices": [{"delta": f"JSON decode error: {str(e)}"}]}
                    else:
                        if response.status != 200:
                            error_text = await response.text()
                            yield {"choices": [{"delta": f"API error: {response.status} - {error_text[:200]}"}]}
                        else:
                            async for line in response.content:
                                line = line.decode('utf-8', errors='replace').strip()
                                if line.startswith('data: '):
                                    if line == 'data: [DONE]':
                                        break
                                    try:
                                        json_str = line[6:]
                                        chunk = json.loads(json_str)
                                        yield chunk
                                    except json.JSONDecodeError as e:
                                        yield {"choices": [{"delta": f"JSON decode error: {str(e)}"}]}
            except Exception as e:
                yield {"choices": [{"delta": f"Stream error: {str(e)}"}]}

    async def complete_chat(self, model, messages):
        url = f"{self.api_host}/api/chat/completions"
        headers = await self.get_headers()
        data = {"model": model, "messages": messages, "stream": False}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=data, timeout=60) as response:
                    if response.status == 401:
                        self.mark_rate_limited(self.active_account)
                        self.active_account = await self.get_active_account()
                        return await self.complete_chat(model, messages)
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API error: {response.status} - {error_text[:200]}")
                    # Возвращаем текст ответа напрямую
                    return await response.text()
            except aiohttp.ClientConnectionError as e:
                raise Exception(f"Connection error: {str(e)}")
            except Exception as e:
                raise Exception(f"Request error: {str(e)}")