import asyncio
from playwright.async_api import async_playwright
import random
import string
import json
import argparse
import os
from datetime import datetime

async def get_new_credentials():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        await page.goto("https://chat.inceptionlabs.ai/auth", wait_until="domcontentloaded")
        register_button = page.locator("div.mt-4.text-sm.text-center button[type='button']")
        await register_button.wait_for(state="visible", timeout=60000)
        if await register_button.count() == 0:
            print(await page.content())
            raise Exception("Register button not found")
        await register_button.click(timeout=10000)
        await page.wait_for_selector('input[autocomplete="name"]', timeout=30000)
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{username}@example.com"
        password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
        await page.fill('input[autocomplete="name"]', username)
        await page.fill('input[autocomplete="email"]', email)
        await page.fill('input[autocomplete="current-password"]', password)
        create_button = page.locator("button[type='submit']")
        await create_button.wait_for(state="visible", timeout=30000)
        if await create_button.count() == 0:
            print(await page.content())
            raise Exception("Create account button not found")
        await create_button.click(timeout=10000)
        await page.wait_for_url("https://chat.inceptionlabs.ai/*", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        cookies = await context.cookies()
        cookies_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
        bearer_token = cookies_dict.get("token")
        if not bearer_token:
            raise Exception("Bearer token not found in cookies")
        await browser.close()
        return {
            "cookies": cookies_dict,
            "bearer": bearer_token
        }

def load_existing_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {"active": [], "rate_limited": []}

def save_data(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

async def main(count, output_file):
    data = load_existing_data(output_file)
    for _ in range(count):
        try:
            credentials = await get_new_credentials()
            data["active"].append(credentials)
        except Exception as e:
            return
        save_data(data, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate new credentials and save to JSON")
    parser.add_argument("--count", type=int, default=1, help="Number of credentials to generate")
    parser.add_argument("--output", type=str, default="credentials.json", help="Output JSON file path")
    args = parser.parse_args()
    asyncio.run(main(args.count, args.output))