# Crowd-Sourcing Tools

This directory contains some tools to support Crowd Sourcing using CrowdFlower. In particular, some JavaScript to allow a prettier layout of the conversation structure.

## Setup

This is a standard nodejs/yarn project. You need to have installed
`npm` and `node` (Recommended to install using [nvm](https://github.com/creationix/nvm), the node version manager).

Once you have `npm`, install `yarn` and `typescript` globally with:

```shell
npm install -g yarn typescript
```

Then, from this directory, you can setup the this node package with:

```shell
yarn install
```

## Build for CrowdFlower and Local tests

Crowdflower has a special jquery setup, so its different for testing locally than when run in crowdflower. The difference is between concatenating these two files after the generated `app.js` (which has the main part of the code):

* src/jquery_crowdflower_require_hack.js
* src/jquery_localtest_require_hack.js

### Build for crowdflower

```shell
yarn run build:crowdflower
```

Generated files end up in `build/dist/crowdflower.js`. This is what should be copied to the crowdflower JS text box.

## Test Locally

```shell
yarn run build:localtest
```

Generated files end up in `build/dist/localtest.js`.

```shell
yarn run serve:localtest
```

In your browser, then open the URL for the corresponding crowdsourcing job i.e.:

*  http://localhost:8000/src/testdata/test1.html
*  http://localhost:8000/src/testdata/test2.html

And observe the test conversations look right, and that no errors appear in the
JavaScript console.

## Deploy to CrowdFlower

CrowdFlower has 3 sections that need files from this directory need to be copied to the relevant UI input boxes in a CrowdFlower's Job page (afer you run the build command):

* CML: `src/cml{N}.html`
* CSS: `src/style{N}.css`
* JavaScript: `build/dist/crowdflower.js`

Where `{N}` is the corresponding crowdsourcing job.

## Job 1: Predicting future toxicity and measuring disagreement.

Shows the crowdworker a conversation, and asks:

*  This conversation is not primarily in English or is not human readable? (Checkbox)
*  Does this conversation contain a toxic comment? (Yes | No | Uncertain)
*  Do the participants in this conversation disagree with one another? (Yes | No | Uncertain)
*  Is the next comment in this conversation likely to be toxic? (Very likely | Somewhat likely | Somewhat unlikely, Very unlikely)

## Job 2: Assessing the toxicity of a comment and measuring disagreement.

Shows the crowdworker a conversation, highlighting the last comment, and asks:

*  This conversation is not primarily in English or is not human readable? (Checkbox)
*  Is the highlighted comment toxic? (Yes|No|Uncertain)
*  Enter the comment numbers, separated by spaces, of any comments the highlighted comment disagrees with. (free form text box entry)

## Job 3: Assessing paired conversations: current and future toxicity.

This job asks raters to compare two conversations and answer which (if any) contains a toxic comment, and which is most likely to result in a future toxic contribution. In particular, it asks:

*  One of the conversations is not primarily in English or is not human readable. (Checkbox)
*  Which (if any) conversation contains a toxic comment? (Neither | Conversation 1 | Conversation 2 | Both 1 and 2)
*  Which of these conversation is most likely to become toxic? (Conversation 1 | Conversation 2)

### Tool support for job prep

There is a small data preperation script:

```
node build/scripts/job3_csv_to_json.js --in_csv_file ./tmp/conversations_as_json_paired.csv  --out_json_file ./tmp/foo.json --out_csv_file ./tmp/foo.csv
```

`in_csv_file` is expected to be a CSV file with headers: "conversation1", "conversation2", and optionally a third column "thebadconversation". The output is a CSV. If there was a field "thebadconversation", it is renamed "now_toxic_gold". The two fields "conversation1" and "conversation2" are put into a single column, "conversations". The CSV is then ready to be uploaded to crowdflower.

The script also outputs to a JSON file, which can use used to create tests, e.g. like the ones in `src/testdata/conversations_job3_paired_x5.js`.