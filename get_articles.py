import urllib.request
from bs4 import BeautifulSoup
import re
from string import punctuation
from pymorphy2 import MorphAnalyzer
import pandas as pd

punct = punctuation + '«»—…“”*№–'
morph = MorphAnalyzer()


def soup(link):
    doc = urllib.request.urlopen(link)
    page = doc.read().decode('cp1251')
    return BeautifulSoup(page, features="lxml")


def analyze(text):
    words = [word.strip(punct) for word in text.lower().split()]
    parsed_words = []
    for word in words:
        if word != '':
            parsed_word = morph.parse(word)[0]
            lemma = parsed_word.normal_form
            tag = parsed_word.tag.POS
            parsed_words.append((word, str(lemma), str(tag)))
    return parsed_words


# извлекаем с одной страницы ссылки на страницы со статьями
source_page = soup('https://newtimes.ru/rubrics/detail/59195/')
articles = []
for a in source_page.find_all('a', href=True):
    if a['href'].startswith('/articles/'):
        articles.append(a['href'])
articles = list(set(articles))


# извлекаем необходимый для датафрейма контент с каждой страницы со статьями
contents = []
for i in articles:
    article_page = soup('https://newtimes.ru' + i)
    title = article_page.find("title").text
    date_and_author = [i.strip().strip("*") for i in article_page.find_all("h4")[1].text.split("|")]
    date = date_and_author[0]
    author = date_and_author[1] if len(date_and_author) == 2 else ''
    lead = article_page.find("div", {"class": "txtlead"}).text.strip()
    lead = re.sub("\xa0", " ", lead)
    content = article_page.find_all("p")
    body = ''
    for j in content:
        j = j.text
        j = re.sub("\xa0", " ", j)
        body += str(j).strip() + " "
    contents.append(['https://newtimes.ru' + i, title, date, author, lead, body])


# анализируем текст с помощью pymorphy2 и добавляем анализ в отдельную ячейку
for i, article in enumerate(contents):
    contents[i] += [analyze(article[5])]


# создаем датафрейм из списка
data = pd.DataFrame(contents, columns=["url", "title", "date", "author", "lead", "text", "parsed_words"])

# записываем датафрейм в файл
data.to_pickle("articles.pkl")