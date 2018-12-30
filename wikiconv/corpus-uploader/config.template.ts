export const ACCESS_TOKEN='{your figshare token}'

export const GCLOUD_STORAGE_BUCKET='wikidetox-wikiconv-public-dataset'
export const GCLOUD_STORAGE_PATH='dataset'
export const GCLOUD_STORAGE_PATH_TO_FIGSHARE_MAPPING= [
  // 'Path in google cloud storage' : 'Name of Figshare article'
  // 'dataset/Chinese/': 'WikiConv: Chinese',
  // 'dataset/English/': 'WikiConv: English',
  // 'dataset/German/': 'WikiConv: German',
  // 'dataset/Russian/': 'WikiConv: Russian',
  {
    figshare_article_name: 'WikiConv_Greek',
    cloud_storage_dir_path: 'dataset/Greek/',
  },
]
