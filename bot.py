import json
import os
import feedparser
from bs4 import BeautifulSoup
from telegram import Bot
from rss_sources import RSS_SOURCES

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
    if "media_content" in entry:
        return entry.media_content[0].get("url")

    if "enclosures" in entry and entry.enclosures:
        return entry.enclosures[0].get("href")

    soup = BeautifulSoup(entry.get("description", ""), "html.parser")
    img = soup.find("img")
    if img:
        return img.get("src")

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

def post_to_telegram(news):
    bot = Bot(token=TOKEN)
    emoji = EMOJIS[hash(news["title"]) % len(EMOJIS)]

    caption = (
        f"{emoji} *{news['title']}*\n\n"
        f"{news['description']}\n\n"
        f"🔗 [Читать полностью]({news['link']})"
    )

    bot.send_photo(
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

    post_to_telegram(news)

    storage[news["link"]] = True
    save_storage(storage)

    print("✅ Новость опубликована")
