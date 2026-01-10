# parsers.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta

# --- Вспомогательная функция для разбора дат (без изменений) ---
def parse_date_string(date_str):
    if not date_str:
        return None
    date_str = date_str.lower().strip()
    MONTHS = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    if 'сегодня' in date_str: return datetime.now()
    if 'вчера' in date_str: return datetime.now() - timedelta(days=1)
    try:
        parts = date_str.split()
        if len(parts) == 3 and parts[1] in MONTHS:
            return datetime(int(parts[2]), MONTHS[parts[1]], int(parts[0]))
    except (ValueError, IndexError): pass
    try:
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError: pass
    return None

# --- Функции ОБНАРУЖЕНИЯ (без изменений) ---
# ... (discover_supersadovnik_links, discover_botanichka_links и т.д. остаются прежними)

# --- Функции ПАРСИНГА отдельных статей (С ИСПРАВЛЕНИЯМИ) ---

def safe_join(paragraphs):
    """Безопасно соединяет текстовые блоки, игнорируя None."""
    text_parts = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        if text:  # Добавляем только если текст не пустой и не None
            text_parts.append(text)
    return '\n\n'.join(text_parts)

def parse_supersadovnik(soup):
    title_tag = soup.find('h1')
    if not title_tag: raise ValueError("Не найден заголовок (h1)")
    title = title_tag.get_text(strip=True)
    
    content_div = soup.find('div', class_='article__text')
    if not content_div: raise ValueError("Не найден основной блок контента")
    
    paragraphs = content_div.find_all(['p', 'h2', 'h3'])
    content = safe_join(paragraphs) # Используем безопасную функцию
    return title, content

def parse_botanichka(soup):
    title_tag = soup.find('h1', class_='post-title')
    if not title_tag: raise ValueError("Не найден заголовок")
    title = title_tag.get_text(strip=True)
    
    content_div = soup.find('div', class_='post-content')
    if not content_div: raise ValueError("Не найден основной блок контента")

    if content_div.find('div', class_='read-also'):
        content_div.find('div', class_='read-also').decompose()
        
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    # Здесь join немного другой, поэтому логику встраиваем прямо сюда
    text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
    content = '\n'.join(text_parts).replace('\n', '\n\n')
    return title, content

def parse_ogorod_ru(soup):
    title_tag = soup.find('h1')
    if not title_tag: raise ValueError("Не найден заголовок")
    title = title_tag.get_text(strip=True)
    
    content_div = soup.find('div', class_='article-body-content-inner')
    if not content_div: raise ValueError("Не найден основной блок контента")
        
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = safe_join(paragraphs)
    return title, content

def parse_dolinadad(soup):
    title_tag = soup.find('h1', class_='blog-post__title')
    if not title_tag: raise ValueError("Не найден заголовок")
    title = title_tag.get_text(strip=True)
    
    content_div = soup.find('div', class_='blog-post__content')
    if not content_div: raise ValueError("Не найден основной блок контента")

    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = safe_join(paragraphs)
    return title, content
    
def parse_tk_konstruktor(soup):
    title_tag = soup.find('h1')
    if not title_tag: raise ValueError("Не найден заголовок")
    title = title_tag.get_text(strip=True)
    
    content_div = soup.find('div', class_='post-content')
    if not content_div: raise ValueError("Не найден основной блок контента")

    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = safe_join(paragraphs) # Используем безопасную функцию
    return title, content


# --- Остальная часть файла (без изменений) ---

def get_html_soup(url):
    # ...
def discover_new_articles(target_url):
    # ...
def parse_article(url):
    # ...
