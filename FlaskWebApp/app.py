import pandas as pd
import config  # make sure to create a config.py file with the settings you got for Azure Cosmos DB
import os
import azure.cosmos.cosmos_client as cosmos_client
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory


from google.cloud import language_v1
import os
from gnews import GNews

now = datetime.now()

app = Flask(__name__)

####################
default_language = "en"
default_results = 20
default_topic = "tesla news"
####################

### Azure Cosmos DB ###
HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']

client = cosmos_client.CosmosClient(
    HOST, {'masterKey': MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
db = client.get_database_client(DATABASE_ID)
# print('Database with id \'{0}\' was found'.format(DATABASE_ID))
container = db.get_container_client(CONTAINER_ID)


### Google Credentials ###
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "creds.json"


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
    now = datetime.now()
    entry = {
        'id': str(now.strftime("%Y%m%d%H%M%S")) + "--" + language + "--" + topic.replace(" ", "-"),
        'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
        'language': language,
        'topic': topic,
        'good': good,
        'bad': bad,
        'news': newsitems
    }
    print(entry.get('id'))
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


def query_items(container, language='', items=24):
    if language == '':
        items = list(container.query_items(
            query="SELECT top " + str(items) + " c.timestamp, c.language, c.good, c.bad, c.id FROM c order by c.timestamp desc", enable_cross_partition_query=True
        ))
    else:
        items = list(container.query_items(
            query="SELECT top " + str(items) + " c.timestamp, c.language, c.good, c.bad, c.id FROM c where c.language = '" + language + "' order by c.timestamp desc", enable_cross_partition_query=True
        ))
    return items


def query_newsdetails(container, myId):
    items = list(container.query_items(
        query="SELECT c.news FROM c where c.id = '" + myId + "'", enable_cross_partition_query=True
    ))
    return items


@app.route('/privacy.html', methods=("POST", "GET"))
def privacy():
    return render_template('privacy.html')


@app.route('/cookies.html', methods=("POST", "GET"))
def cookies():
    return render_template('cookies.html')


@app.route('/ads.txt', methods=("POST", "GET"))
def ads():
    return "google.com, pub-2687895404343958, DIRECT, f08c47fec0942fa0"


@app.route('/', methods=("POST", "GET"))
def html_table():
    language = request.args.get('language')
    if not language:
        language = 'en'
    x = query_items(container, language)

    languageMap = {
        'en': 'English',
        'de': 'German',
        'fr': 'French',
        'es': 'Spanish',
        # 'it': 'Italian',
        # 'nl': 'Dutch',
        # 'pt': 'Portuguese',
        # 'ru': 'Russian',
        # 'ja': 'Japanese',
        'zh': 'Chinese'
    }
    languageLong = languageMap.get(language)

    df = pd.DataFrame(x)

    # calculate FudQ
    df['FudQ'] = ((df['bad']+df['good'])/4) * df['bad']

    fudqavg = df['FudQ'].mean().round(1)
    # fudavg as degree
    fudavgdeg = (fudqavg/100)*180

    fudavgcolor = '#00FF00'
    if fudavgdeg > 120:
        fudavgcolor = '#FF0000'
    elif fudavgdeg > 45:
        fudavgcolor = '#FFFF00'

    df['FudQ'] = df['FudQ'].round(1)
    df['FudQ'] = df['FudQ'].astype(str)
    df['FudQ'] = df['FudQ'].str.replace('inf', '∞')
    df['FudQ'] = df['FudQ'].str.replace('nan', '∞')

    return render_template('fud.html', titles=df.columns.values, row_data=list(df.values.tolist()), link_column="id", zip=zip, fudQAverage=fudqavg, langlong=languageLong, fudAverageDeg=fudavgdeg, fudColor=fudavgcolor, language=language)


@app.route('/graphData.csv', methods=("POST", "GET"))
def graphData():
    language = request.args.get('language')
    if not language:
        language = 'en'
    x = query_items(container, language, 4*12*7)

    df = pd.DataFrame(x)
    df['FudQ'] = ((df['bad']+df['good'])/4) * df['bad']
    df['FudQ'] = df['FudQ'].round(1)
    df['FudQ'] = df['FudQ'].astype(str)
    df['FudQ'] = df['FudQ'].str.replace('inf', '∞')
    df['FudQ'] = df['FudQ'].str.replace('nan', '∞')

    # new df with date and fudq only:
    df2 = df[['timestamp', 'FudQ']]
    df2['timestamp'] = pd.to_datetime(df2['timestamp'])
    df2['timestamp'] = df2['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    # sort by date
    df2 = df2.sort_values(by=['timestamp'])

    return df2.to_csv(index=False)


@app.route('/showNewsDetails', methods=("POST", "GET"))
def fudnews():
    id = request.args.get('id')
    # print("##############" + str(id))

    if id:
        print('Request for fudnews details page received with id=%s' % id)
        x = query_newsdetails(container, id)
        df = pd.DataFrame(x)['news']

        newf = pd.DataFrame()
        for i in range(len(df)):
            newf = newf.append(df[i], ignore_index=True)

        newf = newf.drop(['sentiment', 'publisher', 'description'], axis=1)
        newf['sentimentText'] = newf['sentimentText'].str.replace(
            'good', '👍 good')
        newf['sentimentText'] = newf['sentimentText'].str.replace(
            'bad', '👎 bad')

        # bring df in new order
        newf = newf[['sentimentText', 'url', 'title']]

        colTitles = ['Sentiment', 'Link', 'Title']

        return render_template('fudNewsDetails.html', titles=colTitles, row_data=list(newf.values.tolist()), link_column="Link", title_col="Title", myId=id, zip=zip)
    else:
        print('Request for fudnews details page received with no id -- redirecting')
        return redirect(url_for('fud'))


@app.route('/favicon.ico', methods=("POST", "GET"))
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/sentiment', methods=("POST", "GET"))
def sentiment():
    now = datetime.now()

    specs = []
    spec = {"language": "zh", "results": default_results, "topic": "特斯拉"}
    specs.append(spec)
    spec = {"language": "en", "results": default_results, "topic": default_topic}
    specs.append(spec)
    spec = {"language": "de", "results": default_results, "topic": default_topic}
    specs.append(spec)
    spec = {"language": "fr", "results": default_results, "topic": default_topic}
    specs.append(spec)
    spec = {"language": "es", "results": default_results, "topic": default_topic}
    specs.append(spec)
    print(specs)

    res = ""

    for spec in specs:
        res = res + "\nProcessing " + spec["language"]
        try:
            # print("Processing", spec["language"], spec["results"], spec["topic"])
            result = getJSON(spec["language"], spec["results"], spec["topic"])
            # print(result)
            container.create_item(body=result, indexing_directive="include")
        except Exception as e:
            res = res + "\n" + str(result) + "\n## ERROR ##" + str(e)
    return ('Done!  \n' + res)


if __name__ == '__main__':

    app.run()
