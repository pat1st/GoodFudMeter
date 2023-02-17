// const axios = require('axios');
// const cheerio = require('cheerio');
const path = require('path');
const news = require('gnews');
const {
    LanguageServiceClient
} = require('@google-cloud/language');
const languageClient = new LanguageServiceClient();
const {
    convert
} = require('html-to-text');

/*
how to use:
- install dependencies
    npm i path gnews @google-cloud/language html-to-text
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
            details.push({
                title: article.title,
                fudMeter: 'BAD',
                score
            });
            badCount++;
        } else {
            details.push({
                title: article.title,
                fudMeter: 'GOOD',
                score
            });
            goodCount++;
        }
    }

    return {        
        result: `FUD METER => b:g  ${badCount}:${goodCount}`,
        details,
    };
}


async function analyzeSentiment(content) {
    const [result] = await languageClient.analyzeSentiment({
        document: {
            content,
            type: 'PLAIN_TEXT',
        },
    });

    return result.documentSentiment.score;
}

 //launchAlgo().then(console.log).catch(console.error);


module.exports = async function (context, req) {
    context.log('JavaScript HTTP trigger function processed a request.');

    // const name = (req.query.name || (req.body && req.body.name));
    // const responseMessage = name
    //     ? "Hello, " + name + ". This HTTP triggered function executed successfully."
    //     : "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.";

    const respMsg = await launchAlgo();

    context.res = {
        // status: 200, /* Defaults to 200 */
        body: respMsg
    };
}