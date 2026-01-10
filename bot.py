# bot.py

import os
import json
import random
import telegram
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta

from parsers import discover_new_articles, parse_article
from target_pages import TARGET_PAGES

# --- Конфигурация ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("ИМЯ_ВАШЕГО_СЕКРЕТА") # <-- Не забудьте проверить имя секрета
STORAGE_FILE = "storage.json"
DAYS_LIMIT = 90

# --- Функции для работы с хранилищем ---

def load_posted_articles():
    """Загружает список уже опубликованных URL из storage.json."""
    if not os.path.exists(STORAGE_FILE):
        return []
    try:
        with open(STORAGE_FILE, 'r') as f:
            data = json.load(f)
            # Убедимся, что это список (на случай пустого файла)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

def save_posted_articles(posted_urls):
    """Сохраняет обновленный список URL в storage.json."""
    with open(STORAGE_FILE, 'w') as f:
        json.dump(posted_urls, f, indent=2)

async def main():
    """Главная функция, выполняющая всю работу."""
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Ошибка: BOT_TOKEN или CHANNEL_ID не найдены.")
        return

    print("=== ЗАПУСК ДИНАМИЧЕСКОГО ПАРСЕРА ===")
    
    posted_urls = load_posted_articles()
    print(f"Загружено {len(posted_urls)} уже опубликованных статей.")

    # --- Шаг 1: ОБНАРУЖЕНИЕ ---
    print("Начинаю сканирование целевых страниц...")
    all_discovered_articles = []
    for page in TARGET_PAGES:
        try:
            new_articles = discover_new_articles(page)
            all_discovered_articles.extend(new_articles)
            print(f"  Найдено {len(new_articles)} статей на {page}")
        except Exception as e:
            print(f"  Не удалось просканировать {page}. Ошибка: {repr(e)}") # Используем repr для безопасности
            
    # --- Шаг 2: ФИЛЬТРАЦИЯ ПО ДАТЕ ---
    print(f"\nНачинаю фильтрацию. Всего найдено {len(all_discovered_articles)} статей.")
    recent_articles = []
    limit_date = datetime.now() - timedelta(days=DAYS_LIMIT)
    
    for url, article_date in all_discovered_articles:
        if article_date and article_date > limit_date:
            recent_articles.append(url)
            
    print(f"Найдено {len(recent_articles)} статей, опубликованных за последние {DAYS_LIMIT} дней.")
    
    unique_recent_urls = set(recent_articles)

    # --- Шаг 3: ФИЛЬТРАЦИЯ ПО "ПАМЯТИ" ---
    unposted_articles = [url for url in unique_recent_urls if url not in posted_urls]
    
    if not unposted_articles:
        print("Новых, еще не опубликованных статей в заданном диапазоне дат не найдено. Завершаю работу.")
        return

    print(f"Найдено {len(unposted_articles)} новых статей для публикации.")
    
    # --- Шаг 4: ПУБЛИКАЦИЯ ---
    url_to_post = random.choice(unposted_articles)
    print(f"Выбрана случайная статья для парсинга: {url_to_post}")
    
    formatted_article, error = parse_article(url_to_post)
    
    if error:
         print(f"Не удалось спарсить статью. Пропускаем. Сообщение: {error}")
         return
         
    # Отправляем в Telegram
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        
        if len(formatted_article) > 4096:
            text_to_send = formatted_article[:4000] + "\n\n...(статья слишком длинная, полная версия по ссылке)"
        else:
            text_to_send = formatted_article

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text_to_send,
            parse_mode='Markdown'
        )
        
        print(f"Статья успешно опубликована в канале {CHANNEL_ID}.")
        
        posted_urls.append(url_to_post)
        save_posted_articles(posted_urls)
        print("Файл 'storage.json' обновлен.")

    except Exception as e:
        # === ИСПРАВЛЕНИЕ ЗДЕСЬ ===
        # Используем repr(e), чтобы безопасно напечатать любой объект ошибки
        print(f"!!! Произошла ошибка при отправке в Telegram: {repr(e)}")

    print("=== РАБОТА БОТА ЗАВЕРШЕНА ===")

if __name__ == '__main__':
    asyncio.run(main())
