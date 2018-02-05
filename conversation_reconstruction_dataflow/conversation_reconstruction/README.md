# Conversation Constructor for Wikipedia Talk Pages

This is the codebase for the dataflow pipeline working on constructing conversations from Wikipedia Talk Pages.

Run it with 'python dataflow_main.py --setup_file ./setup.py', you can select a week in 2001 to 2017 to process, using parameters 'week' and 'year'. Revisions from the same page must be processed sequentially in temporal order.

The code will read from a join of the following two tables: 
- A table with all revisions ingested in JSON format from wikipedia data dump.
- A table with page states of previous reconstructed revisions.

The workflow can be seen in the following picture:

![conversation_construction_workflow](docs/workflow.png)

# Output Sample
- [Reconstructed result](https://bigquery.cloud.google.com/table/wikidetox-viz:wikidetox_conversations.reconstructed_at_week5_year2001?pli=1&tab=preview)
- [Existed Page States](https://bigquery.cloud.google.com/table/wikidetox-viz:wikidetox_conversations.page_states?pli=1)
