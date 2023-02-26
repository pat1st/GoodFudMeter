# pip install google.cloud.language
# pip install gnews
# pip install azure-cosmos


from google.cloud import language_v1
import os
from gnews import GNews
from datetime import datetime

import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
# import datetime

import config  # make sure to create a config.py file with the settings you got for Azure Cosmos DB

####################
default_language = "en"
default_results = 11
default_topic = "tesla news"
####################

now = datetime.now()

### Azure Cosmos DB ###
HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']

client = cosmos_client.CosmosClient(
    HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
db = client.get_database_client(DATABASE_ID)
print('Database with id \'{0}\' was found'.format(DATABASE_ID))
container = db.get_container_client(CONTAINER_ID)


### Google Credentials ###
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
    mySentiment = sentiment.score * (1+sentiment.magnitude)
    return mySentiment


def getFudMeterEntry(language, topic, good, bad, newsitems):

    entry = {
        'id': str(now.strftime("%Y%m%d%H%M%S")) + "--" + language + "--" + topic.replace(" ", "-"),
        'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
        'language': language,
        'topic': topic,
        'good': good,
        'bad': bad,
        'news': newsitems
    }
    return entry


def getJSON(language, results, topic):
    good = 0
    bad = 0
    news = get_news(language=language, topic=topic, results=results)
    sentimentText = "neutral"

    newsitems = []

    for newsitem in news:
        cutPos = newsitem['title'].rfind('-')
        mySentimentText = newsitem['title'][0:cutPos] + \
            " " + newsitem['description']
        # print(mySentimentText)
        mySentiment = sample_analyze_sentiment(mySentimentText, language)
        # print(mySentiment)
        if mySentiment >= 0:
            good += 1
            sentimentText = "good"
        else:
            bad += 1
            sentimentText = "bad"

        newsitems.append({
            'title': newsitem['title'],
            'url': newsitem['url'],
            'published date': newsitem['published date'],
            'description': newsitem['description'],
            'publisher': newsitem['publisher'],
            'sentiment': mySentiment,
            'sentimentText': sentimentText
        })

    result = getFudMeterEntry(language, topic, good, bad, newsitems)
    return result


if __name__ == "__main__":

    specs = []
    spec = {"language": "en", "results": default_results, "topic": default_topic}
    specs.append(spec)
    spec = {"language": "de", "results": default_results, "topic": default_topic}
    specs.append(spec)
    spec = {"language": "fr", "results": default_results, "topic": default_topic}
    specs.append(spec)
    spec = {"language": "es", "results": default_results, "topic": default_topic}
    specs.append(spec)

    for spec in specs:
        result = getJSON(spec["language"], spec["results"], spec["topic"])
        print(result)
        container.create_item(body=result)
