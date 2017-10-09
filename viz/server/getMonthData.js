const tasks = require('../wikiDataCollector/tasks');

class GetMonthData {

    getCommentsMinified(data) {

        let monthsData = data[0];
        let revertedData = data[1];
        let nonToxicCount = data[2][0].count;

        let reverted = {};

        revertedData.forEach((d) => {
            reverted[d.revision_id] = true;
        });

        let toxicComments = [];
        let commentsMin = monthsData.map(function (d, i) {
            d.timestamp = d.timestamp.value
            var minData = [1];
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
            toxicComments: toxicComments,
            commentsMin: commentsMin,
            nonToxicCount: nonToxicCount
        };

    }

    getCalanderDataCombined(data) {
        const totalCounts = data[0];
        const revertdCounts = data[1];

        let dates = {}
        totalCounts.forEach((row) => {
            dates[row.month + '/' + row.year] = {
                total: row.total,
                toxic: row.toxic
            }
        });
        revertdCounts.forEach((row) => {
            dates[row.month + '/' + row.year].reverted = row.count;
        });

        let calendarData = [];
        Object.keys(dates).forEach((key) => {
            let ele = dates[key];
            ele.date = key;
            calendarData.push(ele);
        });
        return calendarData;
    }
    get(currentMonth, cb) {
        let st = new Date();

        let month = new Date(currentMonth).getMonth() + 1;
        let year = new Date(currentMonth).getFullYear();
        let dateStr = month + '/01/' + year;

        let startTime = new Date(dateStr);
        let endTime = new Date(dateStr);
        endTime.setMonth(startTime.getMonth() + 1);

        tasks.getMonthData(startTime, endTime, (err, data) => {
            if (!err) {
                let minifiedComments = this.getCommentsMinified(data);
                cb(err, minifiedComments);
                return;
            } else {
                cb(err, null);
            }
        });

    }

    getCalendarData(cb) {
        tasks.getCalendarData((err, data) => {
            if (!err) {
                let calendarData = this.getCalanderDataCombined(data);
                cb(err, calendarData);
                return;
            } else {
                cb(err, null);
            }
        });
    }
}

module.exports = GetMonthData;
