This is a package used for wiki talk page conversation reconstruction given ingested json files, and running locally on a server with 80 cores and 1 TB RAM.

Installation
------------

    pip install -r requirements.txt

    git clone https://github.com/vegetable68/mwparserfromhell

Inside mwparserfromhell: ``python setup.py install``

Running the Pipeline
--------------------

1. **Get Input Filelist**: get_chunk_list_for_processing.py
2. **Reconstruct the Conversations from Ingested Json**: processing_pipeline.py
3. **Group Reconstructed Data into Conversations**: group_data_into_conversations.py

Functionalities
---------------

1. **Testing Utilities**
    * *test_utils.query.get_revisions(talk page title : string) : string, list of dicts*

      Given the title of the talk page, returns the namespace of the page and a list of revisions, with the same format as in samples/input_sample.json

2. **Conversation_Constuctor**
    * Initialize with an optional comment tracking file, which will keep track of all the comments happened in this page in history. Default value is ``None``, format as in tracked_history_comments_samples.json
    * *process(revision : dict, DEBUGGINGMODE = False)* 

      Given the revision with the same format as in samples/input_sample.json, returns a list of actions being done in this revision, samples in samples/action_samples.json  
    * *save(FILENAME : string)* 

      Given the filename, store the intermediate result into the file, format as in samples/intermediate_result.json
    * *load(FILENAME : string, COMMENT_TRACKING_FILE : string)* 

      Given the filename, load the previous intermediate result, if there was a comment tracking file, load the history comments as well, otherwise has the default value ``None``.

3. **Show Your Conversations**
    * *group_into_conversations( page_id : string, action_list : list of dicts)* 

      Given the page id of the talk page and the list of actions(same format as in samples/action_samples.json), returns the a list of conversations(same format as in samples/conversation_samples.json) and a conversation mapping of the actions.
    * *generate_snapshots( conversation : list of dicts)*

      Given the a conversation(same format as the items in samples/conversation_samples.json), generate list of snapshots of this conversation(same format as in samples/conversation_snapshots.json).

In general, check this ipython notebook : Conversation Reconstruction -- Sample Output.ipynb for more information. 

Action Types
------------

An action on the talk page is one of the following types:

* Section Creation
  
  An action that creates the section, the 'content' field records the heading of the section. 

* Comment Adding

  An action that adds an original comment to the page.

* Comment Removal 

  An action that deletes a previously added comment.

* Comment Modification

  An action that modifies a previously added comment.

* Comment Rearrangment
  
  An action that rearranges a previously added comment to a different position on page.

* Comment Restoration
  
  An action that restores a previously deleted comment.

All the actions have the following fields:

* indentation: Level of indentation of the comment, a section creation has indentation level -1.
* rev_id: The revision id of where the action is done.
* id: The id of the action is of the form rev_id.token_offset.
* content: The content of the comment being affected by the action.
* user_id: The id of the user who did the action. 
* user_text: The name of the user who did the action.
* timestamp: The timestamp when the action was happened.
* type: The type of the action, must be one of the types that listed before.
* replyTo_id: The action id of which the current action is replying to, if the action is comment adding or comment modification.
* parent_id: The action id of which added in the previouly added comment that being affect in the current action, if the action is a comment deletion, comment rearragement, comment modification or comment restoration.
* page_id: The id of the page where the action was done.
* page_title: The title of the page where the action was done.


