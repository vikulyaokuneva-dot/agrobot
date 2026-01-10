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
CHANNEL_ID = os.getenv("CHANNEL_ID") # Убедитесь, что имя секрета верное
STORAGE_FILE = "storage.json"
DAYS_LIMIT = 90 # Глубина поиска в днях

# --- Функции для работы с хранилищем (без изменений) ---
def load_posted_articles():
    # ...
def save_posted_articles(posted_urls):
    # ...

async def main():
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
            # Теперь получаем список кортежей (url, date)
            new_articles = discover_new_articles(page)
            all_discovered_articles.extend(new_articles)
            print(f"  Найдено {len(new_articles)} статей на {page}")
        except Exception as e:
            print(f"  Не удалось просканировать {page}. Ошибка: {e}")
            
    # --- Шаг 2: ФИЛЬТРАЦИЯ ПО ДАТЕ ---
    print(f"\nНачинаю фильтрацию. Всего найдено {len(all_discovered_articles)} статей.")
    recent_articles = []
    limit_date = datetime.now() - timedelta(days=DAYS_LIMIT)
    
    for url, article_date in all_discovered_articles:
        # Проверяем, что дата была извлечена и она не старше лимита
        if article_date and article_date > limit_date:
            recent_articles.append(url)
            
    print(f"Найдено {len(recent_articles)} статей, опубликованных за последние {DAYS_LIMIT} дней.")
    
    # Убираем дубликаты, если одна статья на нескольких страницах
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
        # ... (код отправки, обрезки и сохранения остается таким же)
        
        print("Статья успешно опубликована!")
        posted_urls.append(url_to_post)
        save_posted_articles(posted_urls)
        print("Файл 'storage.json' обновлен.")

    except Exception as e:
        print(f"!!! Ошибка при отправке в Telegram: {e}")

    print("=== РАБОТА БОТА ЗАВЕРШЕНА ===")

if __name__ == '__main__':
    asyncio.run(main())
