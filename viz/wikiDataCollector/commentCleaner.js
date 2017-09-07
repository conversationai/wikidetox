// jshint esnext:true
/*global require, define,module*/

const wtf_wikipedia = require("wtf_wikipedia");
const $ = require('cheerio');

class CleanComments {


    removeDate(text) {
        return text.replace(/\d\d:\d\d,( \d?\d)? (.*)( \d?\d)?,? \d\d\d\d (\(UTC\))?/g, '');
    }

    removeSpecialCharsPre(text) {
        text = text.replace(/\| /g, '');
        text = text.replace(/--/g, '');
        text = text.replace(/^[\*:;<|# ]+/, ' ');
        text = text.replace(/}[\*:;<|# ]+/, '}');

        return text;
    }

    removeSpecialCharsPost(text) {
        text = text.replace(/==/g, '');
        text = text.trim();
        return text;
    }

    getCommentTextFromHtml(wikiText) {
        let text = '';

        $(wikiText).find('td.diff-addedline').each(function (i, ele) {
            text += $('<div>' + $(ele).text() + '</div>').text();
        });

        return text;
    }

    getPlanText(wikiText) {

        let text = this.getCommentTextFromHtml(wikiText);

        text = this.removeSpecialCharsPre(text);

        text = wtf_wikipedia.plaintext(text);

        text = this.removeSpecialCharsPost(text);

        text = this.removeDate(text);

        text = text.substring(0, 2800); // COMMENT_ANALYZER_URL limit

        return text;

    }
}

module.exports = CleanComments;
