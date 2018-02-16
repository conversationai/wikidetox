# Conversation Constructor for Wikipedia Talk Pages

This is the codebase for the dataflow pipeline working on constructing conversations from Wikipedia Talk Pages.

Run it with 'python dataflow_main.py --setup_file ./setup.py' 

The code will read from a join of the following two tables: 
- A table with all revisions ingested in JSON format from wikipedia data dump.
- A table with page states of previous reconstructed revisions.

The workflow can be seen in the following picture:

![conversation_construction_workflow](docs/workflow.png)

# Parameters of the code

## Job category
  Specify which kind of data you are processing.
  --category CATEGORY   Specify the job category: long (pages), short (pages),test.

## Parameters for testing

  --save_res_to_cloud   Save the page states result to Cloud as well, if you are not confident of the results yet, save it to the cloud to separate from the page states table where the following reconstruction might depend on it.
  --save_input_to_cloud Save the inputs to Cloud, no processing will be run if this is turned on. This is for you to prepare for testing. 
  --load_input_from_cloud Read input from Cloud.

## Input Parmeters
  --input_table Input table with ingested revisions.
  --input_page_state_table Input page states table from previous reconstruction process.
  --last_revision_table  The table you want to store and read from for the last revision that was processed on each page.
  --page_states_output_table Output page state table for reconstruction.

## Parameters for the time period to run
  You can select any arbitrary week(ranging from 1 to 53) in 2001 to 2017 to process, using parameters 'week' and 'year'. Revisions from the same page must be processed sequentially in temporal order. Thus make sure you've processed all the data before week W from year Y, stored all the page states into a page state table, then start running processing on week W and year Y, otherwise sanity checks in the code will assert errors. 
 
  --week WEEK           The week of data you want to process
  --year YEAR           The year that the week is in

  You can select any arbitrary week range from Wl at year Yl to Wu at year Yu, same as the week and year parameter, make sure you've processed all the data before Wl at year Yl. If you've defined week and year already, the code will process the specific week of the year you defined before.

  --week_lowerbound LOWER_WEEK The start week of data you want to process
  --year_lowerbound LOWER_YEAR The year of the start week.
  --week_upperbound UPPER_WEEK The end week of data you want to process
  --year_upperbound UPPER_YEAR The year of the end week.

  If you run more weeks in a batch, make sure the pages don't get too long otherwise it will exceed the memory limit of dataflow. But running more weeks in one batch is more time and cost efficient, we provide a parameter WEEK_STEP indicate how many weeks you want to run in one batch.

  --week_step WEEK_STEP


# Input Sample
- [Ingested data dump](https://bigquery.cloud.google.com/table/wikidetox-viz:wikidetox_conversations.ingested_test)
- [Reconstructed page states table](https://bigquery.cloud.google.com/table/wikidetox-viz:wikidetox_conversations.page_states_test)
- [Last processed revisions](https://bigquery.cloud.google.com/table/wikidetox-viz:wikidetox_conversations.test_last_revision)

# Output Sample
- You can find your reconstructed results in wikidetox-viz-dataflow/reconstructed_res/reconstruction-from-{category}-pages-week{LOWER_WEEK}year{LOWER_YEAR}-week{UPPER_WEEK}year{UPPER_YEAR} 
- The updated page states will be appended to [Reconstructed page states table](https://bigquery.cloud.google.com/table/wikidetox-viz:wikidetox_conversations.page_states_test)
- [Last processed revisions](https://bigquery.cloud.google.com/table/wikidetox-viz:wikidetox_conversations.test_last_revision) will be updated.

If you run with -save_res_to_cloud, the two tables won't be updated.

# Efficient Reconstruction Approach

The reconstruction job was parallelized by the pages, and the reconstruction speed on each page largely depends on the number and total size of revisions on a certain page. Since the distribution of number of revisions of each page is not uniform for Wikipedia data, we divided pages into three categories for more efficient reconstruction because of the constraint on memory of dataflow jobs.

- Short pages: Pages with fewer than 100 revisions in total.
- Long pages: Pages with more than 100 revisions but fewer than 100,000 reivisions in total.
- Gigantic pages: Pages with more than 100,000 revisions in total, note that there are only two pages of this kind in our dataset(the talk page of the founder of Wikipedia and Main Page.)

We suggest running the short pages in year by year(see recommended parameter settings in scripts/short.sh), long pages week by week(see recommended parameter settings in scripts/long.sh). For gigantic pages we process them individually and suggest running it with direct runner(dataflow_gigantic.py).


# Scripts to run different options

We provide three scripts for you to run on different data in scripts/.

- test.sh: Running test.sh will test on a small portion of data, we suggest changing the runner into DirectRunner for more efficient testings. 
- short.sh: This will process the relatively short pages, we suggest running with more weeks(~1 year) in one batch.
- long.sh: This will process the relatively longer pages, we suggest running with one week in one batch.

# Debugging on a certain page

If you want to debug on a certain page during a certain time: 

- Select revisions to be processed to an ingested table, last processed revisions to last processed revision table, last processed page state to a page state table. Change the parameter accordingly in the test.sh.
- Change your runner to be DirectRunner
- Turn on save_input_to_cloud and run test.sh.
- Turn on load_input_from_cloud, save_res_to_cloud and start testing. 
- Turn on DEBUGGING_MODE in the processor.process() function inside ParDo will give you more details on the processing progress.

- 
