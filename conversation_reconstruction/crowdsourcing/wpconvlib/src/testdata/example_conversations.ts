import * as conversation from "../conversation";

// Note: this is a hacked-up, simple, and not real conversation.
export const example_conversation1: conversation.Conversation = {
  "550613551.0.0": {
    "id": "550613551.0.0",
    "content": "== Name == ",
    "comment_type": "COMMENT_MODIFICATION",
    "user_text": "Adamdaley",
    "timestamp": "2013-04-16 08:55:31 UTC",
    "parent_id": "",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "675014505.416.416": {
    "id": "675014505.416.416",
    "content": " I edited it to the largest \"labor\" uprising and the largest \"organized armed uprising\" since the civil war. They were not in rebellion per se and the race riots of the 60's are clearly a larger uprising (I'm not too sure on armed).",
    "comment_type": "COMMENT_ADDING",
    "user_text": "70.151.72.162",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "parent_id": "550613551.0.0",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "685549021.514.514": {
    "id": "685549021.514.514",
    "content": "Edited it to say \"one of the largest, organized, and well-armed uprisings.\" This seemed like the best course of action. It may be settling but hopefully it resolves the dispute.  \u2014\u00a0Preceding [WIKI_LINK: Wikipedia:Signatures@unsigned] comment added by ",
    "comment_type": "COMMENT_MODIFICATION",
    "user_text": "SineBot",
    "timestamp": "2015-10-13 13:57:01 UTC",
    "parent_id": "675014505.416.416",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "700660703.8.8": {
    "id": "700660703.8.8",
    "content": " The 1877 national railroad strike was the largest armed labor conflict in US History,",
    "comment_type": "COMMENT_ADDING",
    "user_text": "71.112.208.136",
    "timestamp": "2016-01-19 21:26:43 UTC",
    "parent_id": "550613551.0.0",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  }
}



export const example_conversation2: conversation.Conversation = {
  "550613551.0.0": {
    "id": "550613551.0.0",
    "content": "== Name == ",
    "comment_type": "COMMENT_MODIFICATION",
    "user_text": "Adamdaley",
    "timestamp": "2013-04-16 08:55:31 UTC",
    "parent_id": "",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "675014505.416.416": {
    "id": "675014505.416.416",
    "content": " I edited it to the largest \"labor\" uprising and the largest \"organized armed uprising\" since the civil war. They were not in rebellion per se and the race riots of the 60's are clearly a larger uprising (I'm not too sure on armed).",
    "comment_type": "COMMENT_ADDING",
    "user_text": "70.151.72.162",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "parent_id": "550613551.0.0",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "675014505.20.416": {
    "id": "675014505.20.416",
    "content": "Edited it to say \"one of the largest, organized, and well-armed uprisings.\" This seemed like the best course of action. It may be settling but hopefully it resolves the dispute.  \u2014\u00a0Preceding [WIKI_LINK: Wikipedia:Signatures@unsigned] comment added by ",
    "comment_type": "COMMENT_MODIFICATION",
    "user_text": "SineBot",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "parent_id": "675014505.416.416",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  }
}


export const example_conversation3: conversation.Conversation = {
  "675014505.416.416": {
    "id": "675014505.416.416",
    "content": "foo comment 1 text",
    "comment_type": "COMMENT_ADDING",
    "user_text": "70.151.72.162",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "parent_id": "",
    "page_title": "talk page title",
  },
  "675014505.20.416": {
    "comment_type": "COMMENT_MODIFICATION",
    "content": "foo comment 2 text",
    "id": "675014505.20.416",
    "page_title": "talk page title",
    "parent_id": "",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "user_text": "SineBot",
  }
}

export const example_conversation4: conversation.Conversation = {
  "159766698.24.0": {
    "comment_type": "COMMENT_ADDING",
    "content": "\nYour recent edit to [WIKI_LINK: Barton on Sea] ([EXTERNAL_LINK: diff]) was reverted by an automated bot. The edit was identified as adding either test edits, [WIKI_LINK: WP:VAND@vandalism], or [WIKI_LINK: WP:SPAM@link spam] to the page or having an inappropriate [WIKI_LINK: WP:ES@edit summary]. If you want to experiment, please use the preview button while editing or consider using the [WIKI_LINK: Wikipedia:Sandbox@sandbox]. If this revert was in error, please contact the bot operator. If you made an edit that removed a large amount of content, try doing smaller edits instead. Thanks! //",
    "id": "159766698.24.0",
    "page_title": "User talk:213.40.118.71",
    "parent_id": null,
    "timestamp": "2007-09-23T09:05:52.000Z",
    "user_text": "VoABot II",
  },
  "159766698.0.0": {
    "comment_type": "SECTION_CREATION",
    "content": "\n==Regarding your edits to [WIKI_LINK: Barton on Sea]:==",
    "id": "159766698.0.0",
    "page_title": "User talk:213.40.118.71",
    "parent_id": null,
    "timestamp": "2007-09-23T09:05:52.000Z",
    "user_text": "VoABot II",
  }
}