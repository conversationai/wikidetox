
import * as schedule from "node-schedule";
import { Tasks } from "../wikiDataCollector/tasks";

const tasks = new Tasks();

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

        tasks.doStreaming(startTime, endTime, (err, data) => {

            if (err) {
                console.log(err);
                console.log(`Cannot do streaming for interval : ${startTime}  - ${endTime}`)
                return;
            }
            let et = new Date();
            console.log("Finished : streaming wiki data at", new Date());
            let rowsAdded = 0;
            try {
                rowsAdded = data.result.match(/\d+/)[0];
            } catch (e) {
                console.log(e);
            }

            tasks.logStreamTask({
                cron_runtime: data.timeTook,
                end_time: new Date(endTime),
                rows_added: Number(rowsAdded),
                start_time: new Date(startTime),
                timestamp: et,
            });

            tasks.flagReverted(cb);
        });

    }

    public runJob(config: any) {

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
        return true;
    }
    public startScheduleTask(): void {
        schedule.scheduleJob(this.streamWikiDataScheduleTime, this.runJob);
    }
}
