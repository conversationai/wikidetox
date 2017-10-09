// [START app]
'use strict';
const path = require('path');
const express = require('express');
const app = express();
const bodyParser = require('body-parser');
const request = require('request');

const config = require('../config/default');

const CronJobs = require('./cronJobs');

const GetMonthData = require('./getMonthData');

const scheduleCronJobs = new CronJobs();

const getMonthData = new GetMonthData();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
    extended: true
}));
app.use(express.static(path.join(__dirname, '../http-pub')));
app.use('../http-pub', express.static('../http-pub'));

app.get('/', function (req, res) {
    res.sendFile('index.html');
});


// start schedule tasks
app.get('/tasks/hourly', function (req, res) {
    console.log('Received cron call at : ', new Date());
    if (req.get('X-Appengine-Cron')) {
        scheduleCronJobs.runJob();
    } else {
        console.log('Received cron call from unknown : ', new Date());
    }
    res.sendStatus(200);
});

app.get('/getTime', function (req, res) {
    res.send(new Date());
});

app.get('/monthsdata', function (req, res) {
    let startDate = req.query.st;

    getMonthData.get(startDate, (err, data) => {
        if (err) {
            res.status(403).send(err);
            return;
        } else {
            res.send(data);
        }
    })
});

app.get('/calendar', function (req, res) {
    getMonthData.getCalendarData((err, data) => {
        if (err) {
            res.status(403).send(err);
            return;
        } else {
            res.send(data);
        }
    })
});
app.post('/feedback', function (req, res) {
    const comment = req.body.comment;
    const isToxic = req.body.toxic === 'true';
    const revid = req.body.revid;

    const url = config.SUGGEST_SCORE_URL + config.API_KEY;

    if (comment) {
        var feedback = {
            "comment": {
                "text": comment
            },
            "attributeScores": {
                "TOXICITY": {
                    "summaryScore": {
                        "value": isToxic ? 1 : 0
                    }
                }
            },
            "clientToken": "detoxviz-revid-" + revid
        };
        console.log(feedback)
        request({
            url: url,
            method: "POST",
            json: true,
            body: feedback
        }, function (error, response, body) {

            if (error) {
                console.error('Cannot send the feedback', { error: error });
                res.status(400).send('Cannot send the feedback');
                return;
            }
            if (body.error) {
                console.error('Cannot send the feedback', { error: body.error });
                res.status(400).send('Cannot send the feedback');
                return;
            }

            res.send(body);
        });
    } else {
        res.status(400);
    }

});


// Start the server
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`App listening on port ${PORT}`);
});
