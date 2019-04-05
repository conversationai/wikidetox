# WikiConv

WikiConv is a multilingual corpus encompassing the history of conversations on Wikipedia Talk Pages—including the deletion, modification and restoration of comments.

The dataset and reconstruction process for the corpus has been published in the paper [WikiConv: A Corpus of the Complete Conversational History of a Large Online
Collaborative Community](https://arxiv.org/abs/1810.13181), presented at [EMNLP 2018](http://EMNLP2018.org).

The work has also been presented at [the June 2018 Wikipedia reasearch
showcase](https://www.mediawiki.org/wiki/Wikimedia_Research/Showcase#June_2018) (the first of this pair of talks describes our work using an earlier version of this dataset to predict [conversations going awry](https://arxiv.org/abs/1805.05345)).

WikiConv is a multilingual corpus, it currently includes all conversations extracted from the 2018-07-01 Wikipedia dumps of: English, Chinese, German, Greek, Russian.

## License

The dataset is released under the [CC0 license v1.0](http://creativecommons.org/publicdomain/zero/1.0/). The content of individual comments is released under the [CC BY-SA license v3.0](https://creativecommons.org/licenses/by-sa/3.0/), consistently with Wikipedia's attribution requirements.

## Downloading the dataset

The data is available for download from
* Google Cloud: https://console.cloud.google.com/storage/browser/wikidetox-wikiconv-public-dataset
* Figshare: https://figshare.com/projects/WikiConv_A_Corpus_of_the_Complete_Conversational_History_of_a_Large_Online_Collaborative_Community/57110

If you believe there is any information in this dataset that should be removed, please file a Github issue in this repository or email `conversationai-questions@google.com`

## Dataset statistics

In [the WikiConv paper](https://arxiv.org/abs/1810.13181) we use a technical definition of a conversation in terms of a section created in a Wikipedia Talk Page. Using that definition, the scale of the dataset is as follows: 

| Language | Talk Pages | Revisions   |   Users   | Conversational Actions | Conversations | Conversations with > 1 participant |
| -------- | ---------- | ----------- | --------- | ---------------------- | ------------- | ---------------------------------- |
|  English | 23,879,193 | 120,167,011 | 4,359,213 |       241,288,668      |   90,930,244  |            48,064,903              |
|  German  |  1,449,874 | 19,138,645  | 1,378,140 |       40,894,283       |   8,603,776   |             7,046,839              |
|  Russian |  1,316,362 | 5,668,182   | 279,123   |       10,849,917       |   4,351,305   |             1,961,593              |
|  Chinese |  2,169,322 | 4,600,192   | 87,005    |       7,731,744        |   3,432,880   |             1,472,086              |
|  Greek   |  120,520   | 525,738     | 24,187    |       951,921          |   351,975     |	         159,522                |

However, note that this may not necessarily match an intuitive definition of what a conversation is; in particular, such discussions may only contain the comments of a single editor (there may not be a reply from anyone someone else). A better estimate for the scale of human conversations can be found with a query of the form: 

```sql
SELECT COUNT(*) FROM
    (SELECT conversation_id, COUNT(DISTINCT user_text) as cnt
    FROM `wikiconv_v2.en_20180701_conv`
    WHERE type = 'ADDITION' or type='CREATION'
    GROUP BY conversation_id)
    WHERE cnt > 1)
```

For the English language dataset, this results in 8.7M rows (conversations with comments from at least two distinct users).

## Dataset format

### Format of the reconstruction actions

Due to Wikipedia's format and editing style, conversations are just snapshots of
a history of edits (or revisions) that take place on a given Talk Page. We
parse these revisions, compute diffs, and categorize edits into 5 kinds of 'actions':

*   `CREATION`: An edit that creates a new section in wiki markup.
*   `ADDITION`: An edit that adds a new comment to the thread of a conversation.
*   `MODIFICATION`: An edit that modifies an existing comment on a Talk Page.
*   `DELETION`: An edit that removes a comment from a Talk Page.
*   `RESTORATION`: An edit (for example, a [revert](https://en.wikipedia.org/wiki/Help:Reverting)) that restores a previously removed comment.

### Schema

Each row of the table corresponds to an action as defined in the section above.
The schema for the table is then:

*   `id`: An id for the action that the row represents.
*   `conversation_id`: The id of the conversation in which the action took
    place. This is usually the id of the first action of the conversation.
*   `page_title`: The name of the Talk Page where the action occurred.
*   `indentation`: In wiki markup, the level of indentation represents the
    reply-depth in the conversation tree.
*   `replyTo_id`: The id of the action that this action is a reply to.
*   `content`: The text of the comment or section underlying the action.
*   `cleaned_content`: The text of the comment or section underlying the action
    without MediaWiki markup.
*   `user_text`: The name of the user that made the edit from which the action
    was extracted.
*   `rev_id`: The Wikipedia revision id of the edit from which the action was
    extracted.
*   `type`: The type of action that the row represents. This will be one of the
    types enumerated in the previous section.
*   `user_id`: The Wikipedia id of the user making the edit from which the
    action was extracted.
*   `page_id`: The Wikipedia id of the page on which the action took place.
*   `timestamp`: The timestamp of the edit from which the action was extracted.
*   `parent_id`: For modification, removal, and restoration actions, this
    provides the id of the action that was modified, removed, or restored
    respectively.
*   `ancestor_id`: For modification, removal, and restoration actions, this
    provides the id of first creation of the action that was modified, removed,
    or restored respectively.
*   `toxicity`: Score assigned by [Perspective API](https://www.perspectiveapi.com/)
    given the content using TOXICITY attribute (only available for English corpus).
*   `severe_toxicity`: Score given by [Perspective API](https://www.perspectiveapi.com/)
    given the content using SEVERE_TOXICITY attribute (only available for English corpus).

*The thresholds used in the paper are 0.64 and 0.92 for toxicity and severe_toxicity respectively.*

## Visualization of the English Dataset

You can play with our [visualization of the English
Dataset](http://conv-view.wikidetox-viz.appspot.com/). This data represents conversations whose comments have been scored by the
[Perspective API](https://www.perspectiveapi.com/) so you can now browse the comments by toxicity level.
You can click on the comment to see the whole conversation in which it occurs; click on the link to be directed to the revision when this comment was posted. You can also search comments by page or user.

*If you find a comment that contains personal information, please
contact us at yiqing(at)cs(dot)cornell(dot)edu and we will notify the Wikimedia Foundation, as well as remove it from this dataset.*

This system is still under development, any suggestions are welcome!

## The Conversation Reconstruction Process

The code in this repository contains a python package that has reconstruction tools to extract the conversation structure
from Wikipedia talk pages.

Please note that this package (currently) uses Python 2.7.

This reconstruction tool aims to show Wikipedia conversations with their full
history; namely also including not just new posts, but also modifications, deletions and reverts.
For example, rather than showing a snapshot of a conversation, such as:

![Figure1](slides/original_conv.png)

The WikiConv dataset includes all the actions led to its final state:

![Figure2](slides/reconstructed.png).

### Setup the environment

In the *current directory*:

- Follow the steps in [setting up your python dataflow cloud project](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python). Note that *do not proceed* to install the newest google cloud dataflow, which may be in-compatible with some of the packages listed in `requirements.txt`.
- Use your service account to set up boto:
  `gsutil config -e`
- Setup your python2.7 [virtualenv environment](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/) with the `requirements.txt` dependenies installed to run the pipeline:

    ```bash
    # Create virtual env in a filder called `.pyenv`
    python2.7 -m virtualenv .pyenv
    # Enter your python virtual environment.
    .pyenv/bin/activate
    # Install dependenies.
    pip install -r requirements.txt
    # ... do stuff like run the pipline....
    deactivate
    ```

### Run the pipeline
- Copy the template configuration `template.config` to `config/wikiconv.config` e.g. using
  ```
  rsync --ignore-existing ./template.config ./config/wikiconv.config
  ```
  and then edit the configuration for your cloud resources.
- Run: `run_pipeline.sh`
