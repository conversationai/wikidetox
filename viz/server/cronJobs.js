var schedule = require('node-schedule');

const tasks = require('../wikiDataCollector/tasks');

const config = require('../config/default');

class ScheduleTask {

    constructor() {
        var rule = new schedule.RecurrenceRule();
        rule.minute = 10;
        this.streamWikiDataScheduleTime = rule;
    }
    doStreaming(startTime, endTime, cb) {

        console.log('\n');
        let st = new Date();
        console.log('Start: streaming wiki data at ', st);

        tasks.doStreaming(startTime, endTime, function (err, data) {

            if (err) {
                console.log(err);
                console.log('Cannot do streaming for interval : ' + startTime + ' - ' + endTime)
                return;
            }
            let et = new Date();
            console.log('Finished : streaming wiki data at ', new Date());
            let rows_added = 0;
            try {
                rows_added = data.result.match(/\d+/)[0]
            } catch (e) {
                console.log(e);
            }

            tasks.logStreamTask({
                "timestamp": et,
                "cron_runtime": data.timeTook,
                "start_time": new Date(startTime),
                "end_time": new Date(endTime),
                "rows_added": Number(rows_added)
            });

            tasks.flagReverted(cb);
        });

    }

    runJob() {

        let that = this;

        if (new Date() < new Date(config.startStremingTime)) {
            console.log('Will start at ', config.startStremingTime);
            return;
        }


        let startTime = new Date();
        let endTime = new Date();

        startTime.setHours(new Date().getHours() - 2);
        startTime.setMinutes(0);
        endTime.setHours(new Date().getHours() - 1);
        endTime.setMinutes(0);

        that.doStreaming(startTime, endTime, () => {
            console.log('Done');
        });
    }
    startScheduleTask() {
        schedule.scheduleJob(this.streamWikiDataScheduleTime, this.runJob);
    }
}

module.exports = ScheduleTask;
