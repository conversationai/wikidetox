/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define,THREE, brackets: true, $, window, navigator , clearInterval , setInterval,TWEEN, d3*/

define(['./add3DIcons'], function (add3DIcons) {

    "use strict";

    const monthNames = ["January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    function Screens(animate, listiner) {

        this.animate = animate;

        this.listiner = listiner;

        var gTime = Date.now();

        this.changeScreen = function (screen) {
            if (this.OnScreenChange && typeof this.OnScreenChange === 'function') {
                this.OnScreenChange(screen);
            }
        };

        this.logTime = function (me, t) {
            var logTime = t || gTime;
            console.log(me + ' : ', Date.now() - logTime);
        };

        this.setCamera = function (screen) {

            this.animate.controls.reset();

            /*
            if (screen === 2) {
                var target = new THREE.Vector3();
                var position = new THREE.Vector3(-2196.9444248900513, -5783.6378311519475, 4047.1373557078664);
                var up = new THREE.Vector3(0.20125934594291095, 0.5091274844898959, 0.8368296602102624);
                animate.controls.resetTo(target, position, up);
            }*/


        };

        this.setZoom = function () {

        };

        this.bindEvents = function () {
            var that = this;
            $('.backToSphereView').on('click', function () {
                that.switchScreenToSphere();
            });
        };


        this.initScreen = function () {
            this.changeScreen(1);
            this.bindEvents();
        };

    }

    Screens.prototype.hideSphereInfo = function () {
        $('.leftInfoBar, header').fadeOut(200);
    };

    Screens.prototype.switchScreenToComments = function () {
        $('.page').removeClass('active');
        $('#commentScreen').addClass('active');
    };

    Screens.prototype.switchScreenToLoadingScreen = function () {
        $('.page').removeClass('active');
        $('#loadingScreen').addClass('active');
    };

    Screens.prototype.enableControls = function () {
        this.animate.controls.enabled = true;
        this.animate.controls.resetState();
    };

    Screens.prototype.switchScreenToSphere = function () {
        var that = this;
        this.listiner('startSpin');
        $('.page').removeClass('active');
        $('#sphereScreen').addClass('active');
        $('.leftInfoBar, header').fadeIn(700);

        TWEEN.removeAll();
        //this.animate.controls.reset();
        new TWEEN.Tween(this.animate.controls.target).to({
            x: 0,
            y: 0,
            z: 0
        }, 1500).easing(TWEEN.Easing.Exponential.Out).onComplete(that.enableControls.bind(that)).start();

        new TWEEN.Tween(this.animate.camera.position).to({
            x: 0,
            y: 0,
            z: 4500
        }, 1500).easing(TWEEN.Easing.Exponential.Out).start();

        var tokens = window.location.hash.split('/');
        if (tokens[1].match(/(0?[1-9]|[12][0-9]|3[01])[-][0-9]{4}$/)) {
        }
        tokens[2] = '';
        window.location.hash = tokens.join('/');

    };

    Screens.prototype.setLoadingNonToxic = function () {
        $('.leftInfoBar, header').fadeOut(200);
        $('.loadingNontoxic,.loadingReverted,.loadingToxic').removeClass('active');
        $('.loadingNontoxic').addClass('active');
    };
    Screens.prototype.setLoadingReverted = function () {
        $('.leftInfoBar, header').fadeOut(200);
        $('.loadingNontoxic,.loadingReverted,.loadingToxic').removeClass('active');
        $('.loadingReverted').addClass('active');
    };

    Screens.prototype.setLoadingToxic = function () {
        $('.loadingNontoxic,.loadingReverted,.loadingToxic').removeClass('active');
        $('.loadingToxic').addClass('active');
    };

    Screens.prototype.setSphereScreen = function () {
        $('.page').removeClass('active');
        $('#sphereScreen').addClass('active');
        $('.leftInfoBar, header').fadeIn(700);
    };

    Screens.prototype.setCalanderView = function () {
        $('.leftInfoBar, header').fadeOut(200);
        $('.page').removeClass('active');
        $('#calendarScreen').addClass('active');
    };

    Screens.prototype.setCurrentMonthInfo = function (monthYear) {
        let dateObj = new Date(monthYear),
            monthName = monthNames[dateObj.getMonth()]
        $('#currentMonth').text(monthName + ' ' + dateObj.getFullYear())
    };

    Screens.prototype.initCalendarView = function (data) {
        function getMonthHtmlSting(dateStr, monthName, toxic, reverted, nonToxic, percentage) {
            var templ = ` <li data-month="${dateStr}">
                <div class="month">
                    <h2>${monthName}</h2>
                    <span class="toxicScore"> ${percentage}% toxic</span>
                    <div class="monthsDetails">
                        <div class="items">
                            <div class="iconBox iconNonToxic"></div>
                            <span>${nonToxic}</span>
                        </div>
                        <div class="items">
                            <div class="iconBox iconReverted"></div>
                            <span>${reverted}</span>
                        </div>
                        <div class="items">
                            <div class="iconBox iconToxic"></div>
                            <span>${toxic}</span>
                        </div>
                    </div>
                </div>
            </li>`;

            return templ;
        }

        var templ = '';
        var years = {};

        data.forEach(function (month) {

            function pad(n) {
                return (n < 10) ? ("0" + n) : n;
            }

            var monthStr = pad(month.date.split('/')[0]);
            var yearStr = pad(month.date.split('/')[1]);
            var dateStr = '01';

            var dateObj = new Date(monthStr + '/' + dateStr + '/' + yearStr);
            month.dateObj = dateObj;
            month.dateStr = monthStr + '/' + dateStr + '/' + yearStr;


        });

        data.sort(function (a, b) {
            return b.dateObj - a.dateObj;
        });

        data.forEach(function (month) {
            var dateObj = month.dateObj,
                monthName = monthNames[dateObj.getMonth()],
                percentage = ((month.toxic / month.total) * 100).toFixed(2),
                nonToxic = month.total - month.toxic;

            if (!years[dateObj.getFullYear()]) {

                years[dateObj.getFullYear()] = true;
                templ += `<li><label class="yearLabel">${dateObj.getFullYear()}</label></li>`;
            }

            templ += getMonthHtmlSting(month.dateStr, monthName, month.toxic, month.reverted, nonToxic, percentage);
        });

        $("#calendarList").html(templ);

        $('#calendarList .iconToxic').each(function (ele) {
            add3DIcons(this, 'toxic');
        });
        $('#calendarList .iconReverted').each(function (ele) {
            add3DIcons(this, 'nonToxic');
        });

    };

    return Screens;
});
