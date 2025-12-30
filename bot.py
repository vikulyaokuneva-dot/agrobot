import json
import os
import feedparser
import requests
import asyncio
from bs4 import BeautifulSoup
from telegram import Bot

from rss_sources import RSS_SOURCES

SERIES_RULES = {
    "🥔 Неделя картофеля": ["картоф", "клубн"],
    "🌱 Всё о рассаде": ["рассад", "сеян"],
    "🌿 Болезни растений": ["болезн", "гниль", "пятн"],
    "🪴 Полив без ошибок": ["полив", "влаг"],
    "📦 Хранение урожая": ["хранен", "погреб", "подвал"]
}

print("🔥 BOT.PY LOADED 🔥")

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "@helpgardener"
STORAGE_FILE = "storage.json"

EMOJIS = ["🌱", "🪴", "🌼", "🌿", "🍃"]
HASHTAGS = "#сад #огород #дача"

def detect_series(title, text):
    combined = f"{title} {text}".lower()

    for series_name, keywords in SERIES_RULES.items():
        for kw in keywords:
            if kw in combined:
                return series_name

    return None


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

    # 4. og:image со страницы статьи (fallback)
    try:
        print("🔍 Ищу og:image на странице статьи")
        response = requests.get(
            entry.link,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        page = BeautifulSoup(response.text, "html.parser")
        og = page.find("meta", property="og:image")
        if og and og.get("content"):
            print(f"🖼 Найдено og:image: {og['content']}")
            return og["content"]
    except Exception as e:
        print(f"❌ Ошибка при получении картинки: {e}")

    return None


def extract_full_text(url):
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(response.text, "html.parser")

        # удаляем мусор
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        text = "\n".join(
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 40
        )

        return text[:4000]
    except Exception as e:
        print(f"❌ Ошибка извлечения текста статьи: {e}")
        return ""


def summarize_text(text):
    sentences = text.split(".")
    bullets = []

    for s in sentences:
        s = s.strip()
        if 50 < len(s) < 200:
            bullets.append(f"• {s}")

        if len(bullets) >= 5:
            break

    return "\n".join(bullets)


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

            full_text = extract_full_text(link)
            summary = summarize_text(full_text)
            series = detect_series(title, summary)

            if not summary:
                continue

            return {
                "title": title,
                "description": summary,
                "link": link,
                "image": image,
                "series": series
            }

    return None


async def post_to_telegram(news):
    bot = Bot(token=TOKEN)

    emoji = EMOJIS[hash(news["title"]) % len(EMOJIS)]
    series_block = ""
    if news.get("series"):
        series_block = f"{news['series']}\n\n"

    caption = (
        f"{series_block}"
        f"{emoji} *{news['title']}*\n\n"
        f"{news['description']}\n\n"
        f"✍️ Подготовлено на основе материалов: {news['link']}\n\n"
        f"{HASHTAGS}"
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
