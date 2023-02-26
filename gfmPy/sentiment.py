# pip install google.cloud.language
# pip install gnews

from google.cloud import language_v1
import os
from gnews import GNews

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ".\creds.json"


def get_news(language='en', topic='tesla news', results=11):
    news = GNews(language=language, max_results=results)
    tesla = news.get_news(topic)
    return tesla


def sample_analyze_sentiment(content, language="en"):
    client = language_v1.LanguageServiceClient()

    document = language_v1.Document(
        content=content, type_=language_v1.Document.Type.PLAIN_TEXT, language=language)

    response = client.analyze_sentiment(request={"document": document})
    sentiment = response.document_sentiment
    # print("Score: {}".format(sentiment.score))
    # print("Magnitude: {}".format(sentiment.magnitude))
    mySentiment = sentiment.score * (1+sentiment.magnitude)
    # print("Sentiment: {}".format(mySentiment))
    return mySentiment


if __name__ == "__main__":

    language = "en"
    results = 5
    topic = "tesla news"
    

    good = 0
    bad = 0
    news = get_news(language=language, topic=topic, results=results)

    for newsitem in news:
        cutPos = newsitem['title'].rfind('-')
        mySentimentText = newsitem['title'][0:cutPos] + \
            " " + newsitem['description']
        print(mySentimentText)
        mySentiment = sample_analyze_sentiment(mySentimentText, language)
        print(mySentiment)
        if mySentiment >= 0:
            good += 1
        else:
            bad += 1
    print('-----------------')
    print('Good: ' + str(good))
    print('Bad: ' + str(bad))
    
