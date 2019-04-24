export interface ArticleListEntry {
  doi: string,
  thumb: string,
  title: string, // the actual title, matches the config data.
  url: string,
  url_private_api: string,
  defined_type: number, // enum
  url_public_html: string,
  published_date: null | string,
  url_public_api: string,
  group_id: null,
  id: number,
  url_private_html: string
}

export interface UploadPartStatus {
  partNo: number, // parts are indexed from 0 to the final part number.
  startOffset: number, // start byte offset, should be 0 for first part.
  endOffset: number, // final byte offset, should be filesize for last part.
  status: 'PENDING' | 'COMPLETE' | 'ERROR',
  locked: Boolean
}


export interface FileUploadStatus {
  token: string,
  md5: string,
  size: number, // bytes
  name: string, // Figshare name for the file: '13627316/wikiconvel2018070100000of00004',
  status: 'PENDING' | 'COMPLETE' | 'ERROR',
  parts: UploadPartStatus[]
}

export interface FileListEntry {
  status: string, // string enum: 'created' |
  is_link_only: Boolean,
  name: string, // e.g. 'wikiconv-el-20180701--00000-of-00004',
  viewer_type: string // e.g. '',
  preview_state: 'preview_not_available',
  download_url: string,
  supplied_md5: string,
  computed_md5: string,
  upload_token: string,
  upload_url: string, // Can get file upload status from this.
  id: number,
  size: number, // bytes
}

export interface AuthorListEntry {
  url_name: string,
  is_active: Boolean,
  id: number,
  full_name: string, // e.g. 'Lucas Dixon',
  orcid_id: ''
}

export interface Article {
  group_resource_id: null,
  embargo_date: null,
  citation: string, // e.g. 'Dixon, Lucas (2018): WikiConv_Greek. figshare. Fileset.',
  url_private_api: string
  embargo_reason: string, // e.g. ''
  references: [],
  funding_list: [],
  url_public_api: string,
  id: number,
  custom_fields: [],
  size: number, // bytes
  metadata_reason: string,
  funding: null,
  figshare_url: string
  embargo_type: null,
  title: string, // e.g. 'WikiConv_Greek'
  defined_type: number, // enmum
  is_embargoed: Boolean,
  version: string,
  resource_doi: null,
  url_public_html: string,
  confidential_reason: string,
  files: FileListEntry[],
  description: string, // e.g. ''
  tags: [],
  url_private_html: string,
  published_date: null,
  is_active: Boolean,
  authors: AuthorListEntry[],
  is_public: Boolean,
  categories: [],
  thumb: '',
  is_confidential: Boolean,
  doi: '',
  has_linked_file: Boolean,
  license:
   { url: string,
     name: string, // e.g. 'CC BY 4.0',
     value: number // enum I think
  },
  url: string,
  resource_title: null,
  status: 'draft', // string enum
  created_date: string, // e.g. '2018-11-21T10:44:07Z'
  group_id: null,
  is_metadata_record: false,
  modified_date: string, // e.g. '2018-11-21T10:44:07Z'
}

