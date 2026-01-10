# parsers.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Функции ОБНАРУЖЕНИЯ ссылок ---

def discover_supersadovnik_links(soup, base_url):
    links = set()
    for a in soup.find_all('a', class_='item-post-common__title'):
        if a.has_attr('href'):
            links.add(urljoin(base_url, a['href']))
    return list(links)

def discover_botanichka_links(soup, base_url):
    links = set()
    for h2 in soup.find_all('h2', class_='post-title'):
        a = h2.find('a')
        if a and a.has_attr('href'):
            links.add(urljoin(base_url, a['href']))
    return list(links)
    
def discover_ogorod_ru_links(soup, base_url):
    links = set()
    for a in soup.select('.item-article .item-title a, .rubric-popular-item a'):
        if a.has_attr('href'):
             links.add(urljoin(base_url, a['href']))
    return list(links)
    
def discover_dolinadad_links(soup, base_url):
    links = set()
    for a in soup.find_all('a', class_='blog-item__title-link'):
        if a.has_attr('href'):
             links.add(urljoin(base_url, a['href']))
    return list(links)
    
def discover_tk_konstruktor_links(soup, base_url):
    links = set()
    for a in soup.select('.post-item .post-title a'):
        if a.has_attr('href'):
             links.add(urljoin(base_url, a['href']))
    return list(links)


# --- Функции ПАРСИНГА отдельных статей ---

def parse_supersadovnik(soup):
    title = soup.find('h1').get_text(strip=True)
    content_div = soup.find('div', class_='article__text')
    paragraphs = content_div.find_all(['p', 'h2', 'h3'])
    content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
    return title, content

def parse_botanichka(soup):
    title = soup.find('h1', class_='post-title').get_text(strip=True)
    content_div = soup.find('div', class_='post-content')
    if content_div.find('div', class_='read-also'):
        content_div.find('div', class_='read-also').decompose()
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = '\n'.join(p.get_text(strip=True) for p in paragraphs).replace('\n', '\n\n')
    return title, content

def parse_ogorod_ru(soup):
    title = soup.find('h1').get_text(strip=True)
    content_div = soup.find('div', class_='article-body-content-inner')
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = '\n'.join(p.get_text(strip=True) for p in paragraphs).replace('\n', '\n\n')
    return title, content

def parse_dolinadad(soup):
    title = soup.find('h1', class_='blog-post__title').get_text(strip=True)
    content_div = soup.find('div', class_='blog-post__content')
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = '\n'.join(p.get_text(strip=True) for p in paragraphs).replace('\n', '\n\n')
    return title, content
    
def parse_tk_konstruktor(soup):
    title = soup.find('h1').get_text(strip=True)
    content_div = soup.find('div', class_='post-content')
    paragraphs = content_div.find_all(['p', 'h2', 'h3', 'li'])
    content = '\n'.join(p.get_text(strip=True) for p in paragraphs).replace('\n', '\n\n')
    return title, content


# --- Универсальные функции и диспетчеры ---

def get_html_soup(url):
    """Универсальная функция для получения 'супа' со страницы."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers, timeout=15)
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
            return None, "Этот сайт пока не поддерживается для парсинга статей. 😕"
        
        formatted_message = f"**{title.strip()}**\n\n{content.strip()}\n\n[Источник]({url})"
        return formatted_message, None
        
    except Exception as e:
        return None, f"Произошла ошибка при парсинге статьи {url}: {e}."
