export const ACCESS_TOKEN='enter your figshare token'

export const GCLOUD_STORAGE_BUCKET='wikidetox-wikiconv-public-dataset'
export const GCLOUD_STORAGE_PATH='dataset'
export interface FigshareArticleConfig {
  // The name of the figshare article.
  figshare_article_name: string,
  // The google cloud storage path (in GCLOUD_STORAGE_PATH above) where the
  // files to be uploaded are.
  cloud_storage_dir_path: string,
}
export const GCLOUD_STORAGE_PATH_TO_FIGSHARE_MAPPING : FigshareArticleConfig[] =
[
  {
    figshare_article_name: 'WikiConv - English',
    cloud_storage_dir_path: 'dataset/Greek/',
  },
  {
    figshare_article_name: 'WikiConv - Chinese',
    cloud_storage_dir_path: 'dataset/Greek/',
  },
  {
    figshare_article_name: 'WikiConv - Russian',
    cloud_storage_dir_path: 'dataset/Greek/',
  },
  {
    figshare_article_name: 'WikiConv - Geman',
    cloud_storage_dir_path: 'dataset/Greek/',
  },
  {
    figshare_article_name: 'WikiConv - Greek',
    cloud_storage_dir_path: 'dataset/Greek/',
  },
]
