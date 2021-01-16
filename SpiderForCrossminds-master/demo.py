import re
from bs4 import BeautifulSoup
import requests

# print(result)
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/ \
    537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
rawpdfurl = "https://arxiv.org/abs/1912.02424"
abstract = ''
result = response = requests.get(rawpdfurl, headers={'User-Agent': user_agent}).content.decode()
soup = BeautifulSoup(result, 'lxml')
# blockquotes = soup.find('blockquote', class_="abstract mathjax")

# if blockquotes is not None:
#     abstract = blockquotes.contents[2]
#     print(abstract)

authors = ''
div = soup.find('div', class_='authors')
print(div)
a = div.find_all('a')
for i in a:
    authors += i.get_text() + ','
authors = authors[:-1]
print(authors)
