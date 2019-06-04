# Perspective API and Data Loss Prevention(DLP) API

In this directory user can manipulate the perspective and DLP API to detect requested attributes from comments.
Both of these tools are being used in an attempt to detect and prevent doxxing in online conversations,
will be tested in wikipedia chat rooms as a staring point.

1. Install library dependencies:
   ```shell
    pip install -r requirements.txt
    ```
2.[Generate API key](https://github.com/conversationai/perspectiveapi/blob/master/quickstart.md).
   Must first be authenticated with google cloud, [Establish credentials for DLP](https://cloud.google.com/dlp/docs/auth).

3. In a json file store api key and project id:
   ```shell
		{
		"perspective_key": "YOUR API_KEY HERE",
		"project_number": "PROJECT_ID HERE"
		}
    ```
4. Import all required modules:
	![GitHub Logo](/pictures/s1.png)

   Run the given model that that test the comment from the csv file for toxicity and personally identifiable information.

5. Run unittest to ensure the functions contains_toxicity(), and contains_pii(), are working properly.

## Data
Copies of the training and test data are available in Google Storage from the
wikidetox project.

* example.csv : antidox/example.csv
