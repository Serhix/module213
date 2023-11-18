import requests

from bs4 import BeautifulSoup
from .models import Author, Tag, Quote
from datetime import datetime
from time import sleep


def parse_quotes_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for extract in soup.find_all('div', class_='quote'):
            author_link = extract.find('a', text='(about)')
            author_url = f'http://quotes.toscrape.com{author_link["href"]}/'
            print(author_url)
            author = parse_author_page(author_url)
            '''
            без наступного цилку іноді виникала помилка при створенні цитати, автора не встигало підтягувати з бази
            скоріше всього postgres чи docker тормозив
            тому такий костиль
            '''
            while not author:
                try:
                    author = parse_author_page(author_url)
                except:
                    print('не достукались до бази')
                    sleep(1)
            text = extract.find('span', class_='text').get_text(strip=True)
            print(text)
            if not Quote.objects.filter(quote=text).exists():
                Quote(quote=text, author=author).save()
            quote = Quote.objects.get(quote=text)
            print(quote)
            tags = [tag.get_text(strip=True) for tag in extract.find_all('a', class_='tag')]
            for tag in tags:
                tag_obj, created = Tag.objects.get_or_create(name=tag)
                quote.tags.add(tag_obj)

    else:
        print(f"Error requesting URL: {url}")


def parse_author_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        author_details = soup.find('div', class_='author-details')
        fullname = author_details.find('h3', class_='author-title').get_text(strip=True)
        born_date = author_details.find('span', class_='author-born-date').get_text(strip=True)
        born_date = datetime.strptime(born_date, '%B %d, %Y').strftime('%Y-%m-%d')
        born_location = author_details.find('span', class_='author-born-location').get_text(strip=True)
        description = author_details.find('div', class_='author-description').get_text(strip=True)

        if Author.objects.filter(fullname=fullname).exists():
            return Author.objects.filter(fullname=fullname).first()
        else:

            author = Author(
                fullname=fullname,
                born_date=born_date,
                born_location=born_location,
                description=description
            ).save()
            return author

    else:
        print(f"Error requesting URL: {url}")
        return None


def main():
    start_url = 'http://quotes.toscrape.com/'
    while start_url:
        response = requests.get(start_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        parse_quotes_page(start_url)
        next_page = soup.find('li', class_='next')
        if next_page:
            next_url = next_page.find('a')['href']
            start_url = f'http://quotes.toscrape.com{next_url}'
            print(start_url)
        else:
            start_url = None
