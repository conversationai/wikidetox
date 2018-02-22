const fs = require('fs');
const _ = require('lodash');

const readFile = function (name, callback) {

    var fileName = name,
        fullPath = __dirname +'/'+ fileName;

    fs.readFile(fullPath, "utf-8", function (err, data) {
        if (err) {
            throw err;
        }
        callback(data);
    });

};

const writeFile = function (name, content, callback) {


    var fileName = name,
        fullPath = __dirname +'/'+ fileName;

    fs.writeFile(fullPath, content, function (err) {
        if (err) {
            callback(false);
            throw err;
        }
        callback(true);
    });
};


readFile('month.json', function (data) {
    var obj = JSON.parse(data);

    var attackes = 0,
        aggression = 0,
        countb = 0,
        countc = 0;

    var commentsMin = {};

    var min1 = _.values(obj).map(function (d, i) {
        if (d.attack_bool) {
            attackes++;
        }
        if (d.aggression_bool) {
            aggression++;
        }

        if (d.attack_bool && d.aggression_bool) {
           countb++;
        }
        if (d.attack_bool && !d.aggression_bool) {
           countc++;
        }
        var minData =[
            new Date(d.timestamp).getTime() / 1000
            ];
        if (d.aggression_bool || d.attack_bool) {
            minData.push(d.aggression);
            minData.push(d.attack);
            commentsMin[i] = d;
        }

        return minData;
    });

    console.log(attackes, aggression, countb, countc, min1.length)
   /* var bitArray = [];
    min1.forEach(function(d){
        d.forEach(function(d){
            bitArray.push(d);
        });
    });*/

    var minStr = JSON.stringify(min1);

    writeFile('month_min.json', minStr, function (success) {
        console.log(success);
    });

    var minComments = JSON.stringify(commentsMin);
    writeFile('month_comments_min.json', minComments, function (success) {
        console.log(success);
    });
});


/*
[{
        "u": 1,
        "t": "2015-05-14 14:10:44",
        "ag": 0.1215243936,
        "at": 0.1089781225
    }, {
        "u": 1,
        "t": "2015-05-29 03:21:14",
        "ag": 0.0578304939,
        "at": 0.0269095972
    }}

 [
  [1,1431598244000,0.1215243936,0.1089781225],
  [1,1432855274000,0.0578304939,0.0269095972]
]
*/
