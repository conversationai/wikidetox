# Sample Data REAME

This is a data sample from WikiConv, for the submission ***WikiConv: A Corpus of the Complete Conversational History of a Large Online Collaborative Community***.
The sample includes all the actions from the talk page of [Barack Obama](https://en.wikipedia.org/wiki/Barack_Obama) in the first quarter of 2016.
The data has the following schema:

- ID: the unique id of the action.
- Content: the content of the action.
- Type: the type of the action, one of: Creation, Addition, Modification, Deletion, Restoration.
- ReplyTo: the action id to which this action is replying to if any.
- Parent : the action id from which this action was derived if any.
- Revision: the wikipedia revison id where this action took place.
