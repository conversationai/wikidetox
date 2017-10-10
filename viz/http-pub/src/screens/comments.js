/*jslint vars: true, plusplus: true, devel: true, nomen: true, indent: 4, maxerr: 50 */
/*global require, define,THREE, brackets: true, $, window, navigator , clearInterval , setInterval, d3, Float32Array */

define(['three', './toxicObject'], function (THREE, ToxicParticle) {

    "use strict";

    function CommentsView(animate, listiner) {
        var that = this;

        this.commentsData = null;
        this.loadTry = 0;

        this.commentProps = {
            date: null,
            user: null,
            page: null,
            comment: null,
            attackScore: null
        };

        this.currentIndex = -1;
    }

    CommentsView.prototype.addData = function (data) {
        this.commentsData = data;
    };

    CommentsView.prototype.getDataByRevid = function (revid) {
        var comment = this.commentsData.filter(function (c) {
            return c.revision_id === revid;
        });
        if (comment.length) {
            return comment[0];
        }
        return {};
    };
    CommentsView.prototype.getIndexByRevid = function (revid) {
        var index = null;
        this.commentsData.filter(function (c, i) {
            if (c.revision_id === revid) {
                index = i;
            }
        });
        if (!isNaN(index)) {
            return index;
        }
        return;
    };

    CommentsView.prototype.resetData = function () {
        this.commentProps = {
            date: null,
            user: null,
            page: null,
            comment: null,
            attackScore: null
        };
    };

    CommentsView.prototype.setCommentsData = function (index) {
        var that = this;
        if (this.commentsData) {
            var data = this.commentsData[index];

            if (!data) {
                console.error('Cannot get data for index : ', index);
                return;
            }

            this.currentIndex = Number(index);
            this.readAndSetComment(data);
        } else {
            if (this.loadTry > 20) {
                return console.error('Cannot load comments data');
            }
            setTimeout(function () {
                that.loadTry++;
                that.setCommentsData(index);
            }, 100);
        }
    };

    CommentsView.prototype.validateData = function (data) {
        return data.timestamp && data.author && data.page && data.revision_text && data.attack && data.revision_id;
    };


    CommentsView.prototype.readAndSetComment = function (data) {

        this.resetData();
        if (this.validateData(data)) {
            this.commentProps.date = data.timestamp;
            this.commentProps.user = data.author;
            this.commentProps.page = data.page;
            this.commentProps.comment = data.revision_text;
            this.commentProps.attackScore = data.attack;
            this.commentProps.isReverted = data.is_reverted;
            this.commentProps.revisionId = data.revision_id;

        } else {
            console.error("Invalid data", data);
        }

        this.setData();
    };


    CommentsView.prototype.setNextComment = function () {
        var nextiPosition = this.currentIndex + 1,
            nextIndex = this.commentsData[nextiPosition];
        if (nextIndex) {
            this.setCommentsData(nextiPosition);
        }

    };

    CommentsView.prototype.setPreviousComment = function () {
        var previPosition = this.currentIndex - 1,
            previndex = this.commentsData[previPosition];
        if (previndex) {
            this.setCommentsData(previPosition);
        }
    };

    CommentsView.prototype.initBindings = function () {
        $('#top-arrow').on('click touch', this.setPreviousComment.bind(this));
        $('#bottom-arrow').on('click touch', this.setNextComment.bind(this));
        this.seemsWrongInit();
    };

    CommentsView.prototype.seemsWrongInit = function () {
        var that = this;

        $('#cancelDialogue').on('click touch', function () {
            $('.confirmationWrapper').fadeOut();
        });
        $('.confirmationWrapper .close-icon').on('click touch', function (e) {
            e.stopPropagation();
            $('.confirmationWrapper').fadeOut();
        });

        $('.confirmationWrapper #yesToxic').on('click touch', function (e) {
            that.sendFeedBack(true);
            $('.confirmationWrapper').fadeOut();
        });

        $('.confirmationWrapper #notToxic').on('click touch', function (e) {
            that.sendFeedBack(false);
            $('.confirmationWrapper').fadeOut();
        });

    }
    CommentsView.prototype.sendFeedBack = function (isToxic) {
        const comment = this.commentProps.comment;
        const revid = this.commentProps.revisionId;
        $('.seemsWrongBtn').addClass('showFeedBack');
        $('.feedBackThanks').addClass('showFeedBack').fadeIn();
        $.post('/feedback', { toxic: isToxic, comment: comment, revid: revid });
    }


    CommentsView.prototype.setData = function () {


        var commentsProp = this.commentProps;

        var tokens = window.location.hash.split('/');
        tokens[2] = commentsProp.revisionId;
        window.location.hash = tokens.join('/');

        $('.inCopy').remove();

        if (commentsProp.isReverted) {
            $('#commentScreen').addClass('revertedScreen');
        } else {
            $('#commentScreen').removeClass('revertedScreen');
        }
        if ($('.feedBackThanks').hasClass('showFeedBack')) {
            $('.feedBackThanks').removeClass('showFeedBack').hide();
            $('.seemsWrongBtn').removeClass('showFeedBack');
        }

        //create a copy
        $('.dataContent,.labelContent').each(function () {
            var clone = $(this).clone();
            //will add slide out effect
            $(this).after(clone).removeClass('slideIn').addClass('inCopy').attr('id', null);
        });//

        //remove text except the copy
        $('.dataContent:not(.inCopy)').text('');
        $('.dataContent:not(.inCopy),.labelContent:not(.inCopy)').removeClass('slideIn');

        /* $('.dataContent:not(.inCopy),.labelContent:not(.inCopy)').each(function() {
             var clone = $(this).clone();
             $(this).replaceWith(clone);
         });*/

        //add new content (will not add to copy content bcz all ids are removed from copy)
        $('#comment_date').text(commentsProp.date);
        $('#comment_user').text(commentsProp.user);
        $('#comment_page').text(commentsProp.page);
        $('#comment_comment').text(commentsProp.comment);
        $('#comment_attackScore').text(Math.round(100 * (commentsProp.attackScore)) + '%');

        $('#revisionLink').attr('href', 'https://en.wikipedia.org/w/index.php?diff=prev&oldid=' + commentsProp.revisionId);


        //add slide in aimation
        setTimeout(function () {
            $('.dataContent:not(.inCopy),.labelContent:not(.inCopy)').addClass('slideIn');
        }, 50);

        //remove copy
        setTimeout(function () {
            $('.inCopy').remove();
        }, 400);

        $('.seemsWrongBtn').on('click touch', function () {
            $('.confirmationWrapper').fadeIn();
        });


    };


    return CommentsView;

});
