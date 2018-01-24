/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define, brackets: true, $, window, navigator */
require.config({
    baseUrl: './src',
    // urlArgs: "bust=" + (new Date()).getTime(), //prevent cache for testing
    paths: {
        three: '../libs/three',
        jquery: '../libs/jquery'
    }
});

define(['jquery', './animate', './screen', './screens/sphereView', './screens/comments', './controls/guiControls', './add3DIcons'], function (
    $, Animate, Screen, SphereView, CommentsView, GuiControl, add3DIcons) {

    "use strict";

    function App() {

        this.init = function (canvas) {

            var that = this;

            this.eventListiner = function (eventName, data) {
                switch (eventName) {
                    case 'addCommentsData':
                        that.screen.hideSphereInfo();
                        that.commentsView.setCommentsData(data);
                        break;

                    case 'switchScreenToComments':
                        that.screen.switchScreenToComments(data);
                        break;
                    case 'stopSpin':
                        that.sphereView.stopSpin();
                        break;
                    case 'startSpin':
                        that.sphereView.startSpin();
                        break;
                }
            };

            this.gui = new GuiControl();

            this.animate = new Animate(canvas, this.gui);

            this.screen = new Screen(this.animate, this.eventListiner);
            this.screen.OnScreenChange = function (screenNum) {
                that.animate.setScreenLighting(screenNum);
            };
            this.screen.initScreen();

            this.sphereView = new SphereView(this.animate, this.gui, this.eventListiner);

            this.commentsView = new CommentsView(this.animate, this.eventListiner);

            this.animate.renderUpdates.push(this.sphereView.renderUpdates);

            window.animate = this.animate;

            this.currentMonth = null;

        };
    }

    var DetoxViz = new App();

    $(function () {

        var sphereDataLoaded = false;

        $("#container").html('');
        DetoxViz.init($("#container"));

        function initSphereScreen() {
            if (sphereDataLoaded) {
                DetoxViz.screen.setSphereScreen();
                window.dispatchEvent(new Event('resize'));
            } else {
                setTimeout(function () {
                    initSphereScreen();
                }, 200);
            }
        }

        function pad(n) {
            return (n < 10) ? ("0" + n) : n;
        }

        function loadMonth(monthYear, cb) {
            DetoxViz.commentsView.initBindings();

            var loadTime = 1500;
            sphereDataLoaded = false;

            $.get('/monthsdata?st=' + monthYear, function (data) {
                var commentsMin = data.commentsMin;
                var toxicComments = data.toxicComments;
                var nonToxicCount = data.nonToxicCount;

                DetoxViz.commentsView.addData(toxicComments);

                DetoxViz.sphereView.init({
                    toxicComments: toxicComments,
                    nonToxicCount: nonToxicCount
                }, function (dataNumbers) {
                    $('#nonToxicNumber').text(nonToxicCount.toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,').replace('.00', ''));
                    $('#toxicNumber').text(toxicComments.length.toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,').replace('.00', ''));
                    $('#revertedNumber').text(dataNumbers.reverted.toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,').replace('.00', ''));
                    sphereDataLoaded = true;
                    DetoxViz.sphereView.screenInit();
                    cb();
                });


            });

            setTimeout(function () {
                DetoxViz.screen.setLoadingReverted();
                setTimeout(function () {
                    DetoxViz.screen.setLoadingToxic();
                    setTimeout(function () {
                        initSphereScreen();
                    }, loadTime);
                }, loadTime);
            }, loadTime);

            $('body').append(DetoxViz.gui.domElement);

            DetoxViz.screen.setCurrentMonthInfo(monthYear);
        }

        $('#abouLink').on('click', () => {
            $('.page').removeClass('active-out active');
            $('#aboutScreen').addClass('active-out active');
        })
        $('#currentMonth').on('click', function () {
            window.location.hash = '/over-time';
            DetoxViz.screen.setCalanderView();
        });

        function resetAndLoad(monthYear, cb) {
            $("#container").html('').off();
            DetoxViz.init($("#container"));

            DetoxViz.screen.switchScreenToLoadingScreen();
            DetoxViz.screen.setLoadingNonToxic();

            $(DetoxViz.gui.domElement).remove();
            DetoxViz.gui.destroy();

            loadMonth(monthYear, cb);
        }

        var currentMonth = '';
        function readHashAndSetHash() {
            var dateStr = '';
            var goToCommentsScreen = null;
            var index = null;
            var tokens = window.location.hash.split('/');
            if (tokens[1] === 'over-time') {
                DetoxViz.screen.setCalanderView();
                return;
            }
            if (tokens.length === 3 && tokens[2].length > 0) {
                if (currentMonth === tokens[1]) {
                    return;
                } else {
                    goToCommentsScreen = tokens[2];
                }
            }
            if (currentMonth !== '' && currentMonth === tokens[1]) {
                return;
            }

            try {
                dateStr = window.location.hash.split('/')[1];
                if (dateStr.match(/(0?[1-9]|[12][0-9]|3[01])[-][0-9]{4}$/)) {
                    currentMonth = dateStr;
                    DetoxViz.currentMonth = dateStr;
                    resetAndLoad(dateStr.split('-').join('/01/'), function () {
                        if (goToCommentsScreen) {
                            var index = DetoxViz.commentsView.getIndexByRevid(goToCommentsScreen);
                            setTimeout(function () {
                                DetoxViz.eventListiner('addCommentsData', index);
                                DetoxViz.eventListiner('switchScreenToComments', index);
                            }, 1000);
                        }
                    });
                } else {
                    setCurrentDateAsHash();
                }
            } catch (e) {
                setCurrentDateAsHash();
            }
        }

        function setCurrentDateAsHash() {
            var dateObj = currentTime ? new Date(currentTime) : new Date();
            var dateStr = (dateObj.getMonth() + 1) + '/01/' + dateObj.getFullYear();
            window.location.hash = '/' + pad((dateObj.getMonth() + 1)) + '-' + dateObj.getFullYear();
        }

        $(window).on('hashchange', function (e) {
            readHashAndSetHash();
        });

        var currentTime = null;

        $.get('/getTime', function (date) {
            currentTime = date;
            readHashAndSetHash();
        });

        $.get('calendar', function (data) {
            DetoxViz.screen.initCalendarView(data);
            $('#calendarScreen li').on('click', function () {

                var monthYear = $(this).attr('data-month');
                if (!monthYear) {
                    return;
                }
                var dateObj = new Date(monthYear);
                window.location.hash = '/' + pad((dateObj.getMonth() + 1)) + '-' + dateObj.getFullYear();
            });
        });

        $('.iconToxic,.iconReverted').html('')
        $('.iconToxic').each(function (ele) {
            add3DIcons(this, 'toxic');
        });
        $('.iconReverted').each(function (ele) {
            add3DIcons(this, 'nonToxic');
        });

        $('#calendarScreen .backToSphereView').on('click', function () {
            if (DetoxViz.currentMonth) {
                window.location.hash = '/' + DetoxViz.currentMonth
            } else {
                window.location.hash = '/';
            }
        });
    });



});
