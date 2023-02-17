// const axios = require('axios');
// const cheerio = require('cheerio');
const path = require('path');
const news = require('gnews');
const { LanguageServiceClient } = require('@google-cloud/language');
const languageClient = new LanguageServiceClient();
const { convert } = require('html-to-text');

/*
how to use:
- install dependencies
    npm i axios cheerio gnews @google-cloud/language html-to-text
- add the correct crendentials in creds.json
    see Readme.md
- use the following command: 
    node index.js



 to be created in another file called creds.json at the root of this file.
{
  "type": "service_account",
  "project_id": "xx",
  "private_key_id": "xx",
  "private_key": "xx",
  "client_email": "xx",
  "client_id": "xx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "xx",
}

*/

process.env.GOOGLE_APPLICATION_CREDENTIALS = path.join(__dirname, 'creds.json');

async function launchAlgo() {
  const articles = await news.search('tesla news');
  let badCount = 0;
  let goodCount = 0;
  const details = []
  for (const article of articles) {
    //const pageContent = await readPageContent(article.article);
    const score = await analyzeSentiment(article.title);
    /*
      https://cloud.google.com/natural-language/docs/basics#interpreting_sentiment_analysis_values
      Clearly Positive*	"score": 0.8, "magnitude": 3.0
      Clearly Negative*	"score": -0.6, "magnitude": 4.0
      Neutral	"score": 0.1, "magnitude": 0.0
      Mixed	"score": 0.0, "magnitude": 4.0

      For example, you may define a threshold of any score over 0.25 as clearly positive, and then modify the score threshold to 0.15 after reviewing your data and results and finding that scores from 0.15-0.25 should be considered positive as well.
    */
    if (score < 0) {
      details.push({ title: article.title, fudMeter: 'BAD', score });
      badCount++;
    } else {
      details.push({ title: article.title, fudMeter: 'GOOD', score });
      goodCount++;
    }
  }

  return {
    details,
    result: `FUD METER => b:g  ${badCount}:${goodCount}`,
  };
}

// async function readPageContent(link) {
//   const response = await axios.get(link);
//   const googleNewsPageContent = cheerio.load(response.data)
//   const { data } = await axios.get(googleNewsPageContent('c-wiz a[rel=nofollow]').attr('href'));
//
//   const realPageContent = cheerio.load(data)
//   return convert(realPageContent('body').html(), { wordwrap: null });
//
//   //@todo read the correct section for each website
//   // each website has an unique structure
// }

async function analyzeSentiment(content) {
  const [result] = await languageClient.analyzeSentiment({
    document: {
      content,
      type: 'PLAIN_TEXT',
    },
  });

  return result.documentSentiment.score;
}

launchAlgo().then(console.log).catch(console.error);