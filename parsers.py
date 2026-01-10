# parsers.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta

# --- Новая вспомогательная функция для разбора дат ---
def parse_date_string(date_str):
    """
    Пытается разобрать строку с датой в разных форматах.
    Возвращает объект datetime или None, если не удалось.
    """
    date_str = date_str.lower().strip()
    
    # Словарь для русских месяцев
    MONTHS = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }

    if 'сегодня' in date_str:
        return datetime.now()
    if 'вчера' in date_str:
        return datetime.now() - timedelta(days=1)

    try:
        # Попытка разобрать формат "10 января 2024"
        parts = date_str.split()
        if len(parts) == 3 and parts[1] in MONTHS:
            day = int(parts[0])
            month = MONTHS[parts[1]]
            year = int(parts[2])
            return datetime(year, month, day)
    except (ValueError, IndexError):
        pass # Игнорируем ошибку и пробуем следующий формат

    try:
        # Попытка разобрать формат "10.01.2024"
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError:
        pass # Игнорируем

    return None # Если ничего не подошло

# --- Обновленные функции ОБНАРУЖЕНИЯ (теперь возвращают список кортежей (url, date)) ---

def discover_supersadovnik_links(soup, base_url):
    articles = []
    for item in soup.find_all('div', class_='item-post-common'):
        link_tag = item.find('a', class_='item-post-common__title')
        date_tag = item.find('span', class_='item-post-common__date')
        if link_tag and date_tag and link_tag.has_attr('href'):
            url = urljoin(base_url, link_tag['href'])
            date = parse_date_string(date_tag.get_text())
            articles.append((url, date))
    return articles

def discover_botanichka_links(soup, base_url):
    articles = []
    for item in soup.find_all('article'):
        link_tag = item.find('h2', class_='post-title').find('a')
        date_tag = item.find('span', class_='post-meta-date')
        if link_tag and date_tag and link_tag.has_attr('href'):
            url = urljoin(base_url, link_tag['href'])
            date = parse_date_string(date_tag.get_text())
            articles.append((url, date))
    return articles

def discover_ogorod_ru_links(soup, base_url):
    articles = []
    for item in soup.select('.item-article, .rubric-popular-item'):
        link_tag = item.find('a')
        date_tag = item.find('div', class_='item-date')
        if link_tag and date_tag and link_tag.has_attr('href'):
            url = urljoin(base_url, link_tag['href'])
            date = parse_date_string(date_tag.get_text())
            articles.append((url, date))
    return articles

def discover_dolinadad_links(soup, base_url):
    articles = []
    for item in soup.find_all('div', class_='blog-item__inner'):
        link_tag = item.find('a', class_='blog-item__title-link')
        date_tag = item.find('span', class_='blog-item__date')
        if link_tag and date_tag and link_tag.has_attr('href'):
            url = urljoin(base_url, link_tag['href'])
            date = parse_date_string(date_tag.get_text())
            articles.append((url, date))
    return articles

def discover_tk_konstruktor_links(soup, base_url):
    articles = []
    for item in soup.find_all('div', class_='post-item'):
        link_tag = item.select_one('.post-title a')
        date_tag = item.find('span', class_='post-date')
        if link_tag and date_tag and link_tag.has_attr('href'):
            url = urljoin(base_url, link_tag['href'])
            date = parse_date_string(date_tag.get_text())
            articles.append((url, date))
    return articles

# --- Функции парсинга отдельных статей (остаются без изменений) ---
# ... (весь код для parse_supersadovnik, parse_botanichka и т.д. остается прежним)
# --- Универсальные функции и диспетчеры (остаются без изменений) ---
# ... (get_html_soup, discover_new_articles, parse_article)

# --- Вспомогательные функции и диспетчеры (без изменений) ---
def get_html_soup(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')

def discover_new_articles(target_url):
    print(f"  Сканирую {target_url}...")
    soup = get_html_soup(target_url)
    
    if 'supersadovnik.ru' in target_url:
        return discover_supersadovnik_links(soup, target_url)
    elif 'botanichka.ru' in target_url:
        return discover_botanichka_links(soup, target_url)
    # ... и так далее
    else:
        return []

def parse_article(url):
    # ... (эта функция остается без изменений)
