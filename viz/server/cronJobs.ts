
import * as schedule from "node-schedule";

// const tasks = require('../wikiDataCollector/tasks');

export class ScheduleTask {

    public streamWikiDataScheduleTime;

    constructor() {

        const rule = new schedule.RecurrenceRule();
        rule.minute = 10;

        this.streamWikiDataScheduleTime = rule;

    }
    public doStreaming(startTime, endTime, cb): void {

        console.log("\n");
        const st = new Date();
        console.log("Start: streaming wiki data at ", st);

        // tasks.doStreaming(startTime, endTime, function (err, data) {

        //     if (err) {
        //         console.log(err);
        //         console.log('Cannot do streaming for interval : ' + startTime + ' - ' + endTime)
        //         return;
        //     }
        //     let et = new Date();
        //     console.log('Finished : streaming wiki data at ', new Date());
        //     let rows_added = 0;
        //     try {
        //         rows_added = data.result.match(/\d+/)[0]
        //     } catch (e) {
        //         console.log(e);
        //     }

        //     tasks.logStreamTask({
        //         "timestamp": et,
        //         "cron_runtime": data.timeTook,
        //         "start_time": new Date(startTime),
        //         "end_time": new Date(endTime),
        //         "rows_added": Number(rows_added)
        //     });

        //     tasks.flagReverted(cb);
        // });

    }

    public runJob(config: any): void {

        if (new Date() < new Date(config.startStremingTime)) {
            console.log("Will start at ", config.startStremingTime);
            return;
        }

        const startTime = new Date();
        const endTime = new Date();

        startTime.setHours(new Date().getHours() - 2);
        startTime.setMinutes(0);
        endTime.setHours(new Date().getHours() - 1);
        endTime.setMinutes(0);

        this.doStreaming(startTime, endTime, () => {
            console.log("Done");
        });
    }
    public startScheduleTask(): void {
        schedule.scheduleJob(this.streamWikiDataScheduleTime, this.runJob);
    }
}
