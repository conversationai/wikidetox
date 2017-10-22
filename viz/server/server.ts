
import * as express from 'express';
import * as path from 'path';
import * as bodyParser from 'body-parser';
import * as request from 'request';

import { ScheduleTask } from './cronJobs';
import { GetMonthData } from './GetMonthData';

const scheduleCronJobs = new ScheduleTask();
const getMonthData = new GetMonthData();

interface Logger {
    write(s: string): void;
}

interface Config {
    bigQuery: Object,
    startStremingTime: string,
    wiki: Object,
    gcloudKey: string,
    API_KEY: string,
    COMMENT_ANALYZER_URL: string,
    SUGGEST_SCORE_URL: string,
    isProduction: boolean,
    port: string
}

export class Server {
    public app: express.Express
    private log: Logger;
    public port: number;

    constructor(public config: Config) {

        this.initLogger();

        this.app = express();

        this.app.use(bodyParser.json());
        this.app.use(bodyParser.urlencoded({
            extended: true
        }));
        let publicDir = path.join(__dirname, '../../http-pub');
        this.app.use(express.static(publicDir));

        this.app.get('/', function (req, res) {
            res.sendFile('index.html');
        });

        // start schedule tasks
        this.app.get('/tasks/hourly', function (req, res) {
            console.log('Received cron call at : ', new Date());
            if (req.get('X-Appengine-Cron')) {
                scheduleCronJobs.runJob(this.config);
            } else {
                console.log('Received cron call from unknown : ', new Date());
            }
            res.sendStatus(200);
        });

        this.app.get('/getTime', function (req, res) {
            res.send(new Date());
        });

        this.app.get('/monthsdata', function (req, res) {
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

        this.app.get('/calendar', function (req, res) {
            getMonthData.getCalendarData((err, data) => {
                if (err) {
                    res.status(403).send(err);
                    return;
                } else {
                    res.send(data);
                }
            })
        });
        this.app.post('/feedback', function (req, res) {
            this.postFeedback(req, res);
        });

    }
    initLogger() {
        if (this.config.isProduction) {
            this.log = { write: (_s: string): void => { } };
        } else {
            this.log = { write: (s: string): void => { console.log(s); } };
        }
    }
    postFeedback(req, res) {
        const comment = req.body.comment;
        const isToxic = req.body.toxic === 'true';
        const revid = req.body.revid;

        const url = this.config.SUGGEST_SCORE_URL + this.config.API_KEY;

        if (comment) {
            const feedback = {
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
    }
    public start(): Promise<void> {
        return new Promise((resolve, reject) => {
            this.port = parseInt(process.env.PORT) || parseInt(this.config.port);
            this.app.listen(this.port, (err) => {
                if (err) {
                    reject(err);
                } else {
                    console.log(`App listening on port ${this.port}`);
                    resolve(null);
                }
            });
        });
    }


};
