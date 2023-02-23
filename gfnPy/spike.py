# pip install gnews

from gnews import GNews
import json


def get_news(language='en', topic='tesla news', results=11):
    news = GNews(language=language)
    tesla = news.get_news(topic)
    return tesla


teslanews = get_news()
for news in teslanews:
	print(news['title'])
	print(news['url'])
	print(news['published date'])
	print(news['description'])
	print(news['publisher'])
	
	print('-----------------')
# print(teslanews)
