// const tasks = require('../wikiDataCollector/tasks');

export class GetMonthData {
    // TSTODO : define data
    public getCommentsMinified(data: any) {

        const monthsData = data[0];
        const revertedData = data[1];
        const nonToxicCount = data[2][0].count;

        const reverted = {};

        revertedData.forEach((d) => {
            reverted[d.revision_id] = true;
        });

        const toxicComments = [];
        const commentsMin = monthsData.map((d, i) => {
            d.timestamp = d.timestamp.value;
            const minData = [1];
            if (d.attack >= 0.5) {
                minData.push(d.attack);
                d.is_reverted = reverted[d.revision_id];
                if (d.is_reverted) {
                    minData.push(reverted[d.revision_id]);
                }
                toxicComments.push(d);
            }
            return minData;
        }, this);

        return {
            commentsMin,
            nonToxicCount,
            toxicComments,
        };

    }
    // TSTODO : define data
    public getCalanderDataCombined(data: any) {
        const totalCounts = data[0];
        const revertdCounts = data[1];

        const dates = {};
        totalCounts.forEach((row) => {
            dates[row.month + "/" + row.year] = {
                total: row.total,
                toxic: row.toxic,
            };
        });
        revertdCounts.forEach((row) => {
            dates[row.month + "/" + row.year].reverted = row.count;
        });

        const calendarData = [];
        Object.keys(dates).forEach((key) => {
            const ele = dates[key];
            ele.date = key;
            calendarData.push(ele);
        });
        return calendarData;
    }
    public get(currentMonth, cb): void {
        const st = new Date();

        const month = new Date(currentMonth).getMonth() + 1;
        const year = new Date(currentMonth).getFullYear();
        const dateStr = month + "/01/" + year;

        const startTime = new Date(dateStr);
        const endTime = new Date(dateStr);
        endTime.setMonth(startTime.getMonth() + 1);

        // tasks.getMonthData(startTime, endTime, (err, data) => {
        //     if (!err) {
        //         let minifiedComments = this.getCommentsMinified(data);
        //         cb(err, minifiedComments);
        //         return;
        //     } else {
        //         cb(err, null);
        //     }
        // });

    }

    public getCalendarData(cb: (err, data) => void) {
        // tasks.getCalendarData((err, data) => {
        //     if (!err) {
        //         let calendarData = this.getCalanderDataCombined(data);
        //         cb(err, calendarData);
        //         return;
        //     } else {
        //         cb(err, null);
        //     }
        // });
    }
}
