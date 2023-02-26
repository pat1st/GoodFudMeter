#import datetime
import logging
import azure.functions as func
from google.cloud import language_v1
import os
from gnews import GNews
from datetime import datetime
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
#from config import *

settings = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://gfmtdb.documents.azure.com:443/'),
    'master_key': os.environ.get('ACCOUNT_KEY', 'abcxyz=='),
    'database_id': os.environ.get('COSMOS_DATABASE', 'GFMdata'),
    'container_id': os.environ.get('COSMOS_CONTAINER', 'Sentiments'),
}


####################
default_language = "en"
default_results = 11
default_topic = "tesla news"
####################

now = datetime.now()

### Azure Cosmos DB ###
HOST = settings['host']
MASTER_KEY = settings['master_key']
DATABASE_ID = settings['database_id']
CONTAINER_ID = settings['container_id']

client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
db = client.get_database_client(DATABASE_ID)
#print('Database with id \'{0}\' was found'.format(DATABASE_ID))
container = db.get_container_client(CONTAINER_ID)

### Google Credentials ###
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getcwd() + "/TriggerGfmToDb/creds.json"
#################################
def get_news(language='en', topic='tesla news', results=11):
    logging.info('get_news started')
    try:
        news = GNews(language=language, max_results=results)
    except Exception as err:
        logging.info(f"init news: Unexpected {err=}, {type(err)=}")

    logging.info('news object initialized')

    try:
        tesla = news.get_news(topic)
    except Exception as err:
        logging.info(f"get news: Unexpected {err=}, {type(err)=}")
    
    logging.info('news successfully fetched')

    return tesla

def sample_analyze_sentiment(content, language="en"):
    client = language_v1.LanguageServiceClient()

    document = language_v1.Document(content=content, type_=language_v1.Document.Type.PLAIN_TEXT, language=language)

    response = client.analyze_sentiment(request={"document": document})
    sentiment = response.document_sentiment
    mySentiment = sentiment.score * (1+sentiment.magnitude)
    return mySentiment

def getFudMeterEntry(language, topic, good, bad, newsitems):
    logging.info(str(now))
    logging.info(str(now.strftime("%Y%m%d%H%M%S")))

    entry = {
        'id': str(now.strftime("%Y%m%d%H%M%S")) + "--" + language + "--" + topic.replace(" ", "-"),
        'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
        'language': language,
        'topic': topic,
        'good': good,
        'bad': bad,
        'news': newsitems
    }
    logging.info('json entry created')
    return entry


def getJSON(language, results, topic):
    logging.info('getJSON started')
    good = 0
    bad = 0
    try:
        news = get_news(language=language, topic=topic, results=results)
    except Exception as err:
        logging.info(f"call get_news: Unexpected {err=}, {type(err)=}")
    logging.info('news successfully fetched2')

    sentimentText = "neutral"

    newsitems = []
    logging.info('about to iterate the news items')
    for newsitem in news:
        cutPos = newsitem['title'].rfind('-')
        mySentimentText = newsitem['title'][0:cutPos] + \
            " " + newsitem['description']
        #logging.info('sentimentText' + mySentimentText)
        try:
            mySentiment = sample_analyze_sentiment(mySentimentText, language)
        except Exception as err:
            logging.info(f"call sample_analyze_sentiment: Unexpected {err=}, {type(err)=}")

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
    logging.info('collected news items')
    try:
        result = getFudMeterEntry(language, topic, good, bad, newsitems)
    except Exception as err:
        logging.info(f"call getFudMeterEntry: Unexpected {err=}, {type(err)=}")

    return result


#################################
def main(mytimer: func.TimerRequest) -> None:
    logging.info('ok, initialized, beginning to do some work')
    specs = []
    spec = {"language": "en", "results": default_results, "topic": default_topic}
    specs.append(spec)
    #spec = {"language": "de", "results": default_results, "topic": default_topic}
    #specs.append(spec)
    #spec = {"language": "fr", "results": default_results, "topic": default_topic}
    #specs.append(spec)
    #spec = {"language": "es", "results": default_results, "topic": default_topic}
    #specs.append(spec)

    logging.info('specs defined')
    logging.info('now: ' + str(now))

    for spec in specs:
        logging.info('-#-# looking up for language: ' + spec["language"])
        try:
            result = getJSON(spec["language"], spec["results"], spec["topic"])
        except Exception as err:
            logging.info(f"call getJSON: Unexpected {err=}, {type(err)=}")

        logging.info('generated entry for ' + spec["language"] +  "  next step storing to DB")

        try:
            container.create_item(body=result)
        except Exception as err:
            logging.info(f"call container.create_item: Unexpected {err=}, {type(err)=}")
## TODO: does not reach this point, why??
        logging.info('stored DB entry for ' + spec.language)
