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
    "status": "just added",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "675014505.416.416": {
    "id": "675014505.416.416",
    "content": " I edited it to the largest \"labor\" uprising and the largest \"organized armed uprising\" since the civil war. They were not in rebellion per se and the race riots of the 60's are clearly a larger uprising (I'm not too sure on armed).",
    "comment_type": "COMMENT_ADDING",
    "user_text": "70.151.72.162",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "parent_id": "550613551.0.0",
    "status": "just added",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "685549021.514.514": {
    "id": "685549021.514.514",
    "content": "Edited it to say \"one of the largest, organized, and well-armed uprisings.\" This seemed like the best course of action. It may be settling but hopefully it resolves the dispute.  \u2014\u00a0Preceding [WIKI_LINK: Wikipedia:Signatures@unsigned] comment added by ",
    "comment_type": "COMMENT_MODIFICATION",
    "user_text": "SineBot",
    "timestamp": "2015-10-13 13:57:01 UTC",
    "status": "content changed",
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
    "status": "just added",
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
    "status": "just added",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "675014505.416.416": {
    "id": "675014505.416.416",
    "content": " I edited it to the largest \"labor\" uprising and the largest \"organized armed uprising\" since the civil war. They were not in rebellion per se and the race riots of the 60's are clearly a larger uprising (I'm not too sure on armed).",
    "comment_type": "COMMENT_ADDING",
    "user_text": "70.151.72.162",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "parent_id": "550613551.0.0",
    "status": "just added",
    "page_title": "Talk:Teenage Mutant Ninja Turtles II: The Secret of the Ooze",
  },
  "675014505.20.416": {
    "id": "675014505.20.416",
    "content": "Edited it to say \"one of the largest, organized, and well-armed uprisings.\" This seemed like the best course of action. It may be settling but hopefully it resolves the dispute.  \u2014\u00a0Preceding [WIKI_LINK: Wikipedia:Signatures@unsigned] comment added by ",
    "comment_type": "COMMENT_MODIFICATION",
    "user_text": "SineBot",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "status": "content changed",
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
    "status": "just added",
    "page_title": "talk page title",
  },
  "675014505.20.416": {
    "id": "675014505.20.416",
    "content": "foo comment 2 text",
    "comment_type": "COMMENT_MODIFICATION",
    "user_text": "SineBot",
    "timestamp": "2015-08-07 17:03:18 UTC",
    "status": "content changed",
    "parent_id": "",
    "page_title": "talk page title",
  }
}
