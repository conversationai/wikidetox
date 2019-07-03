# Perspective API and Data Loss Prevention(DLP) API

In this directory user can manipulate the perspective and DLP API to detect requested attributes from comments.
Both of these tools are being used in an attempt to detect and prevent doxxing in online conversations,
will be tested in wikipedia chat rooms as a staring point.

1. Install [Bazel](https://docs.bazel.build/versions/master/install.html)

2. [Generate API key](https://github.com/conversationai/perspectiveapi/blob/master/quickstart.md).
   Must first be authenticated with google cloud, [Establish credentials for DLP](https://cloud.google.com/dlp/docs/auth).

3. api_key.json is the file where api key and project id will be stored:
   ```shell
		{
		"perspective_key": "YOUR API_KEY HERE",
		"project_number": "PROJECT_ID HERE"
		}
    ```
    No longer need to aunthenticate with BigQuery because Apache Beam has integration.
    
4. To run the code that processes all comments:
   ``` shell
	bazel run :perspective --input_file=$PWD/example.csv
          --api_key=$PWD/api_key.json
   ```

   Run the given model that test the comment from the csv file for toxicity and personally identifiable information.

5. Run unittest to ensure the functions contains_toxicity(), and contains_pii(), are working properly.
   ```shell
   bazel test :perspective_test --test_output=all
   ```

## Data
Copies of the training and test data are available in Google Storage from the
wikidetox project.

* example.csv : antidox/example.csv
