// jshint esnext:true
/*global require, define,module*/

import * as $ from "cheerio";
import * as wtf_wikipedia from "wtf_wikipedia";

export class CommentCleaner {

    public removeDate(text) {
        return text.replace(/\d\d:\d\d,( \d?\d)? (.*)( \d?\d)?,? \d\d\d\d (\(UTC\))?/g, "");
    }

    public removeSpecialCharsPre(text) {
        text = text.replace(/\| /g, "");
        text = text.replace(/--/g, "");
        text = text.replace(/^[\*:;<|# ]+/, " ");
        text = text.replace(/}[\*:;<|# ]+/, "}");

        return text;
    }

    public removeSpecialCharsPost(text) {
        text = text.replace(/==/g, "");
        text = text.trim();
        return text;
    }

    public getCommentTextFromHtml(wikiText) {
        let text = "";

        $(wikiText).find("td.diff-addedline").each((i, ele) => {
            text += $("<div>" + $(ele).text() + "</div>").text();
        });

        return text;
    }

    public getPlanText(wikiText) {

        let text = this.getCommentTextFromHtml(wikiText);

        text = this.removeSpecialCharsPre(text);

        text = wtf_wikipedia.plaintext(text);

        text = this.removeSpecialCharsPost(text);

        text = this.removeDate(text);

        text = text.substring(0, 2800); // COMMENT_ANALYZER_URL limit

        return text;

    }
}
