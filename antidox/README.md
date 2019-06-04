# Perspective API and Data Loss Prevention(DLP) API

In this directory user can manipulate the perspective and DLP API to detect requested attributes from comments.
Both of these tools are being used in an attempt to detect and prevent doxxing in online conversations,
will be tested in wikipedia chat rooms as a staring point.

1. Install library dependencies:
   ```shell
    pip install -r requirements.txt
    ```
2. [Generate API key](https://github.com/conversationai/perspectiveapi/blob/master/quickstart.md).
   Must first be authenticated with google cloud, [Establish credentials for DLP](https://cloud.google.com/dlp/docs/auth).

3. api_key.json is the file where api key and project id will be stored:
   ```shell
		{
		"perspective_key": "YOUR API_KEY HERE",
		"project_number": "PROJECT_ID HERE"
		}
    ```
4. To run the code that processes all comments:
   ``` shell
	python3 perspective.py
   ```

   Run the given model that test the comment from the csv file for toxicity and personally identifiable information.

5. Run unittest to ensure the functions contains_toxicity(), and contains_pii(), are working properly.
   ```shell
   python3 perspective_test.py
   ```
   or

   ```shell
   python3 -m unittest perspective_test.py
   ```

## Data
Copies of the training and test data are available in Google Storage from the
wikidetox project.

* example.csv : antidox/example.csv
