# parsers.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta

# --- Вспомогательные функции ---

def parse_date_string(date_str):
    """
    Пытается разобрать строку с датой в разных форматах.
    Возвращает объект datetime или None, если не удалось.
    """
    if not date_str:
        return None
    date_str = date_str.lower().strip()
    MONTHS = { 'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12 }
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

def safe_join(paragraphs):
    """Безопасно соединяет текстовые блоки, игнорируя None."""
    text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
    return '\n\n'.join(text_parts)

def escape_markdown(text: str) -> str:
    """Экранирует специальные символы для Telegram MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-.=|{}!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)


# --- Функции ОБНАРУЖЕНИЯ ссылок ---

def discover_supersadovnik_links(soup, base_url):
    articles = []
    for item in soup.find_all('div', class_='item-post-common'):
        link_tag = item.find('a', class_='item-post-common__title')
        date_tag = item.find('span', class_='item-post-common__date')
        if link_tag and date_tag and link_tag.has_attr('href'):
            url = urljoin(base_url, link_tag['href'])
            date = parse_date_string(date_tag.get_text())
            if date:
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
            if date:
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
            if date:
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
            if date:
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
            if date:
                articles.append((url, date))
    return articles


# --- Функции ПАРСИНГА отдельных статей ---

def parse_supersadovnik(soup):
    title_tag = soup.find('h1')
    if not title_tag: raise ValueError("Не найден заголовок (h1)")
    title = title_tag.get_text(strip=True)
    content_div = soup.find('div', class_='article__text')
    if not content_div: raise ValueError("Не найден основной блок контента (div class='article__text')")
    paragraphs = content_div.find_all(['p', 'h2', 'h3'])
    content = safe_join(paragraphs)
    return title, content

def parse_botanichka(soup):
    title_tag = soup.find('h1', class_='post-title')
    if not title_tag: raise ValueError("Не найден заголовок (h1 class='post-title')")
    title = title_tag.get_text(strip=True)
    content_div = soup.find('div', class_='post-content')
    if not content_div: raise ValueError("Не найден основной блок контента (div class='post-content')")
    if content_div.find('div', class_='read-also'):
        content_div.find('div', class_='read-also').decompose()
    text_parts = [p.get_text(strip=True) for p in content_div.find_all(['p', 'h2', 'h3', 'li']) if p.get_text(strip=True)]
    content = '\n'.join(text_parts).replace('\n', '\n\n')
    return title, content

def parse_ogorod_ru(soup):
    title_tag = soup.find('h1')
    if not title_tag: raise ValueError("Не найден заголовок (h1)")
    title = title_tag.get_text(strip=True)
    content_div = soup.find('div', class_='article-body-content-inner')
    if not content_div: raise ValueError("Не найден основной блок контента (div class='article-body-content-inner')")
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = safe_join(paragraphs)
    return title, content

def parse_dolinadad(soup):
    title_tag = soup.find('h1', class_='blog-post__title')
    if not title_tag: raise ValueError("Не найден заголовок (h1 class='blog-post__title')")
    title = title_tag.get_text(strip=True)
    content_div = soup.find('div', class_='blog-post__content')
    if not content_div: raise ValueError("Не найден основной блок контента (div class='blog-post__content')")
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = safe_join(paragraphs)
    return title, content
    
def parse_tk_konstruktor(soup):
    title_tag = soup.find('h1')
    if not title_tag: raise ValueError("Не найден заголовок (h1)")
    title = title_tag.get_text(strip=True)
    content_div = soup.find('div', class_='post-content')
    if not content_div: raise ValueError("Не найден основной блок контента (div class='post-content')")
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = safe_join(paragraphs)
    return title, content


def get_html_soup(url):
    """
    Универсальная функция для получения 'супа' со страницы.
    Теперь с более реалистичными заголовками для обхода защиты.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/'
    }
    response = requests.get(url, headers=headers, timeout=15)
    # Эта строка правильно определит ошибку, если она все же произойдет
    response.raise_for_status() 
    return BeautifulSoup(response.text, 'html.parser')

def discover_new_articles(target_url):
    """Диспетчер обнаружения: вызывает нужный discover-парсер."""
    print(f"  Сканирую {target_url}...")
    soup = get_html_soup(target_url)
    if 'supersadovnik.ru' in target_url:
        return discover_supersadovnik_links(soup, target_url)
    elif 'botanichka.ru' in target_url:
        return discover_botanichka_links(soup, target_url)
    elif 'ogorod.ru' in target_url:
        return discover_ogorod_ru_links(soup, target_url)
    elif 'dolinasad.by' in target_url:
        return discover_dolinadad_links(soup, target_url)
    elif 'tk-konstruktor.ru' in target_url:
        return discover_tk_konstruktor_links(soup, target_url)
    return []

def parse_article(url):
    """Диспетчер парсинга: вызывает нужный parse-парсер для статьи."""
    try:
        soup = get_html_soup(url)
        if 'supersadovnik.ru' in url:
            title, content = parse_supersadovnik(soup)
        elif 'botanichka.ru' in url:
            title, content = parse_botanichka(soup)
        elif 'ogorod.ru' in url:
            title, content = parse_ogorod_ru(soup)
        elif 'dolinasad.by' in url:
            title, content = parse_dolinadad(soup)
        elif 'tk-konstruktor.ru' in url:
            title, content = parse_tk_konstruktor(soup)
        else:
            return None, "Этот сайт пока не поддерживается для парсинга статей."
        
        if not title or not content:
            raise ValueError("Заголовок или контент статьи оказались пустыми после парсинга.")

        safe_title = escape_markdown(title.strip())
        safe_content = escape_markdown(content.strip())
        
        formatted_message = f"*{safe_title}*\n\n{safe_content}\n\n[Источник]({url})"
        return formatted_message, None
        
    except Exception as e:
        return None, f"Произошла ошибка при парсинге статьи {url}: {e}"

