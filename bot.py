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
HASHTAGS = "#сад #огород #дача"

SERIES_RULES = {
    "🥔 Неделя картофеля": ["картоф", "клубн"],
    "🌱 Всё о рассаде": ["рассад", "сеян"],
    "🌿 Болезни растений": ["болезн", "гниль", "пятн"],
    "🪴 Полив без ошибок": ["полив", "влаг"],
    "📦 Хранение урожая": ["хранен", "погреб", "подвал"],
}

SEASON_RULES = {
    "🌱 Весенние работы": {
        "months": [3, 4, 5],
        "keywords": ["рассад", "посад", "гряд", "почв"]
    },
    "☀️ Летний уход": {
        "months": [6, 7, 8],
        "keywords": ["полив", "вред", "болезн", "подкорм"]
    },
    "🍂 Осенний урожай": {
        "months": [9, 10, 11],
        "keywords": ["урожа", "хранен", "уборк", "обрез"]
    },
    "❄️ Зимние советы": {
        "months": [12, 1, 2],
        "keywords": ["комнат", "зим", "хранен", "план"]
    }
}


# ---------- STORAGE ----------

def load_storage():
    if not os.path.exists(STORAGE_FILE):
        return {"posts_count": 0, "published_links": {}}

    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # миграция старого формата
    if "published_links" not in data:
        return {
            "posts_count": len(data),
            "published_links": data
        }

    return data


def save_storage(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def increment_posts_count(storage):
    storage["posts_count"] = storage.get("posts_count", 0) + 1


def should_make_short_post(posts_count):
    return posts_count != 0 and posts_count % 10 == 0


# ---------- SERIES ----------

def detect_series(title, text):
    combined = f"{title} {text}".lower()
    for name, keywords in SERIES_RULES.items():
        for kw in keywords:
            if kw in combined:
                return name
    return None

from datetime import datetime

def detect_season_series(title, text):
    month = datetime.now().month
    combined = f"{title} {text}".lower()

    for season, rule in SEASON_RULES.items():
        if month not in rule["months"]:
            continue

        for kw in rule["keywords"]:
            if kw in combined:
                return season

    return None


# ---------- CONTENT ----------

def clean_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ").strip()


def extract_image(entry):
    if "media_content" in entry:
        media = entry.media_content
        if media and media[0].get("url"):
            return media[0]["url"]

    if "enclosures" in entry and entry.enclosures:
        enc = entry.enclosures
        if enc and enc[0].get("href"):
            return enc[0]["href"]

    soup = BeautifulSoup(entry.get("description", ""), "html.parser")
    img = soup.find("img")
    if img and img.get("src"):
        return img["src"]

    try:
        response = requests.get(
            entry.link,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        page = BeautifulSoup(response.text, "html.parser")
        og = page.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]
    except Exception:
        pass

    return None


def extract_full_text(url):
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        text = "\n".join(
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 40
        )

        return text[:4000]
    except Exception:
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


def get_latest_news(storage):
    for source in RSS_SOURCES:
        feed = feedparser.parse(source)

        for entry in feed.entries:
            link = entry.get("link")
            if not link or link in storage["published_links"]:
                continue

            image = extract_image(entry)
            if not image:
                continue

            title = clean_html(entry.get("title", ""))

            full_text = extract_full_text(link)
            summary = summarize_text(full_text)
            if not summary:
                continue

            series = detect_series(title, summary) or detect_season_series(title, summary)


            return {
                "title": title,
                "description": summary,
                "link": link,
                "image": image,
                "series": series
            }

    return None


# ---------- POSTING ----------

def generate_short_post():
    tips = [
        "Не поливайте растения холодной водой — это стресс для корней.",
        "Лучше недолить растение, чем перелить.",
        "Рыхление почвы после полива улучшает доступ кислорода.",
        "Не сажайте рассаду в холодную землю — рост замедлится.",
        "Пожелтение листьев часто говорит о переувлажнении."
    ]
    return "🌱 *Совет дня*\n\n" + tips[hash(os.urandom(4)) % len(tips)]


async def post_short(text):
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")


async def post_full(news):
    bot = Bot(token=TOKEN)
    emoji = EMOJIS[hash(news["title"]) % len(EMOJIS)]

    series_block = f"{news['series']}\n\n" if news.get("series") else ""

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


# ---------- MAIN ----------

def main():
    print("🚀 Бот запущен")

    if not TOKEN:
        print("❌ BOT_TOKEN не найден")
        return

    storage = load_storage()
    print(f"📦 Постов опубликовано: {storage['posts_count']}")

    if should_make_short_post(storage["posts_count"]):
        print("📝 Короткий пост")
        asyncio.run(post_short(generate_short_post()))
        increment_posts_count(storage)
        save_storage(storage)
        return

    news = get_latest_news(storage)
    if not news:
        print("⚠️ Нет подходящих новостей")
        return

    asyncio.run(post_full(news))
    storage["published_links"][news["link"]] = True
    increment_posts_count(storage)
    save_storage(storage)

    print("✅ Пост опубликован")


if __name__ == "__main__":
    main()
