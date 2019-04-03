# Wiki Categorize

Categorizing wikipedia talk pages, with Google Cloud natrual language processing API.
For a full list of categories, visit [API documentation](https://cloud.google.com/natural-language/docs/categories).

## Package Management

This project uses [Yarn](https://yarnpkg.com) for package mangement. Install with `npm install -g yarn`. 

## Project setup

Run

```
yarn install
```
to install dependencies and create a `yarn.lock` file.

This project relies on Google's [BigQuery API](https://cloud.google.com/bigquery/docs/reference/rest/v2/) to query data via NodeJS. To setup an instance you need a Google Cloud Project with the Perpsective API enabled.

1. Download a service account key under API access in your cloud project, and store it in root folder
2. Go to src/config.ts and fill in the key file path, project ID and data table names.

## Talk page categorization process

This project takes source data from reconstructed wikipedia discussion data dump, processed by [conversation reconstruction method](https://github.com/conversationai/wikidetox/tree/master/wikiconv). This method can be used on any wikipedia talk page data with a page name. 

To categorize talk pages, the scripts follow these steps:

1. Get direct subcategories for each unique talk page with Wikimedia API:
```https://en.wikipedia.org/w/api.php?format=json&action=query&prop=categories&cllimit=max&titles=[PAGE-NAME]```

2. Clean result categories to delete entries irrelevant to page content. These entries usually contain keywords: 
```['Wikipedia', 'AC with', 'CS1', 'Good articles', 'Articles', 'All articles', 'Pages', 'Use mdy dates from', 'Use dmy dates from', 'English from', 'Webarchive template', 'births', 'deaths', 'Redirects']```

Example cleaned results:

Bonsai Kitten:

```["2000 hoaxes", "Cats in popular culture", "Entertainment websites", "Fiction about animal cruelty","Fictional cats", "Fictional companies", "Humorous hoaxes in science"]```

Watergate:

```["Watergate scandal", "Nixon administration controversies", "20th-century scandals", "Political controversies","Political scandals in the United States", "Political terminology of the United States", "1970s in the United States", "News leaks"]```

3. Run cleaned categories and page title as one string through the Google Cloud Natural Language API. The API returns up to 3 relevant category/subcategory/sub-sub category combos with confidence level greater than 0.5. If the page categories are not sufficient for categorization, this step will return null. 

Example returns:

Bonsai Kitten: 

```
/Arts & Entertainment - Confidence:   0.73
/People & Society - Confidence:   0.68
/Hobbies & Leisure - Confidence:   0.65
```

Watergate:

```
/News/Gossip & Tabloid News/Scandals & Investigations - Confidence:   0.97
/Sensitive Subjects - Confidence:   0.93
/News/Politics - Confidence:   0.63
```

Some example results using this method (showing category/subcategory/sub-sub category combo with highest confidence):

| page_title    | category1     | sub_category1  | subsub_category1 |
| --------------------------- | -------------------- | -------------------- | -------------------- |
| Analytical Feminism | People & Society | Social Issues & Advocacy | null |
| Dogwood Alliance | People & Society | Social Issues & Advocacy | Green Living & Environmental Issues |
| Glossary of French expressions in English | Reference | Language Resources | Foreign Language Resources | 
| Horary astrology | People & Society | Religion & Belief | null |
| Lago Petroleum Corporation | Business & Industrial | Energy & Utilities | Oil & Gas |
| Prodromos Meravidis | Arts & Entertainment | Entertainment Industry | Film & TV Industry |

To start categorization process, run:
```
yarn run start
```

## Build files 

To compile typescript files, run:
```
yarn run compile
```

