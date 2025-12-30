import json
import os
import feedparser
import requests
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot

from rss_sources import RSS_SOURCES

print("🔥 BOT.PY LOADED 🔥")



TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "@helpgardener"
STORAGE_FILE = "storage.json"

EMOJIS = ["🌱", "🪴", "🌼", "🌿", "🍃"]

def load_storage():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_storage(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ").strip()

def extract_image(entry):
    # 1. media:content
    if "media_content" in entry:
        media = entry.media_content
        if media and media[0].get("url"):
            return media[0]["url"]

    # 2. enclosure
    if "enclosures" in entry and entry.enclosures:
        enc = entry.enclosures
        if enc and enc[0].get("href"):
            return enc[0]["href"]

    # 3. img в description
    soup = BeautifulSoup(entry.get("description", ""), "html.parser")
    img = soup.find("img")
    if img and img.get("src"):
        return img["src"]

    # 4. og:image со страницы статьи (FALLBACK)
    try:
        print("🔍 Ищу og:image на странице статьи")
        response = requests.get(entry.link, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })
        page = BeautifulSoup(response.text, "html.parser")
        og = page.find("meta", property="og:image")
        if og and og.get("content"):
            print(f"🖼 Найдено og:image: {og['content']}")
            return og["content"]
    except Exception as e:
        print(f"❌ Ошибка при получении картинки: {e}")

    return None

def get_latest_news():
    storage = load_storage()

    for source in RSS_SOURCES:
        feed = feedparser.parse(source)

        for entry in feed.entries:
            link = entry.get("link")
            if not link or link in storage:
                continue

            image = extract_image(entry)
            if not image:
                continue

            title = clean_html(entry.get("title", ""))
            description = clean_html(entry.get("description", ""))[:700]

            return {
                "title": title,
                "description": description,
                "link": link,
                "image": image
            }
    return None

async def post_to_telegram(news):
    bot = Bot(token=TOKEN)

    emoji = EMOJIS[hash(news["title"]) % len(EMOJIS)]
    hashtags = "#сад #огород #дача"

    caption = (
        f"{emoji} *{news['title']}*\n\n"
        f"{news['description']}\n\n"
        f"🔗 [Читать полностью]({news['link']})\n\n"
        f"{hashtags}"
    )

    await bot.send_photo(
        chat_id=CHAT_ID,
        photo=news["image"],
        caption=caption,
        parse_mode="Markdown"
    )

def main():
    print("🚀 Бот запущен")

    if not TOKEN:
        print("❌ BOT_TOKEN не найден")
        return

    storage = load_storage()
    print(f"📦 В storage записей: {len(storage)}")

    news = get_latest_news()

    if not news:
        print("⚠️ Нет подходящих новостей для публикации")
        return

    print(f"📰 Найдена новость: {news['title']}")
    print(f"🖼 Картинка: {news['image']}")

    asyncio.run(post_to_telegram(news))

    storage[news["link"]] = True
    save_storage(storage)

    print("✅ Новость опубликована")


if __name__ == "__main__":
    main()
