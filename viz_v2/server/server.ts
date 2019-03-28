import express = require("express");
import * as bodyParser from "body-parser";
import * as path from "path";

import { BigQueryData } from "./bigQuery";

interface IConfig {
    gcloudKey: string;
    bigQuery: {
        projectId: string;
        datasetID: string;
        dataTable: string;
    },
    port: number
}

export class Server {
    public app: express.Express;
    public bigQuery: any;
    
    constructor (public config: IConfig) {

        this.bigQuery = new BigQueryData(config);

        this.app = express();
        this.app.use(bodyParser.json());
        this.app.use(bodyParser.urlencoded({
            extended: true,
        }));

        const publicDir = path.join(__dirname, "static");
        this.app.use(express.static(publicDir));

        this.app.get("/", (req, res) => {
            res.sendFile(path.resolve("static/index.html"), { root: __dirname });
        });

        this.app.post("/monthsdata", async (req, res) => {
            const startDate = req.body.st || '2018-06-01';
            const endDate = req.body.end || '2018-07-01';
            try {
                const query = this.bigQuery.monthDataQuery(startDate, endDate);
                const rows = await this.bigQuery.queryTable(query);
                console.log(`sending ${rows.length} rows`);
                res.send(rows);
            } catch (err) {
                console.error(err);
                res.status(403).send(err);
            }
        });

        this.app.post("/dailytrends", async (req, res) => {
            const startDate = req.body.st || '2018-06-01';
            const endDate = req.body.end || '2018-07-01';
            try {
                const query = this.bigQuery.dailyTimelineQuery(startDate, endDate);
                const rows = await this.bigQuery.queryTable(query);
                console.log(`sending ${rows.length} rows for daily trends`);
                res.send(rows);
            } catch (err) {
                console.error(err);
                res.status(403).send(err);
            }
        });

        this.app.post("/monthlytrends", async (req, res) => {
            const startDate = req.body.st || '2017-01-01';
            try {
                const query = this.bigQuery.getMonthTimeline(startDate);
                const rows = await this.bigQuery.queryTable(query);
                console.log(`sending ${rows.length} rows for monthly trends`);
                res.send(rows);
            } catch (err) {
                console.error(err);
                res.status(403).send(err);
            }
        });
    }

    public start(): Promise<null> {
        return new Promise((resolve, reject) => {
            const port = process.env.PORT || this.config.port;
            this.app.listen(port, (err) => {
                if (err) {
                    reject(err);
                } else {
                    console.log(`App listening on port ${port}`);
                    resolve(null);
                }
            });
        });
    }
}