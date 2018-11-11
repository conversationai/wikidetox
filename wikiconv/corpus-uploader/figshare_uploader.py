from config.figshare_token import FIGSHARE_TOKEN
from google.cloud import storage
import hashlib
import json
import os

import requests
from requests.exceptions import HTTPError

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string("title", None,
                    "Title of Figshare article.")
flags.DEFINE_string("file", None,
                    "File(s) to upload")

# flags.DEFINE_boolean("is_binary_embedding", False,
#                      "Whether embeddings are binaries.")
# flags.DEFINE_integer("batch_size", 64,
#                      "The batch size to use during training.")


# TODO: use this.
# see: https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/storage/cloud-client/snippets.py


BASE_URL = 'https://api.figshare.com/v2/{endpoint}'


class FishareUploader(object):

  def __init__(self, token, title, file_path, chunk_size=1048576):
    self.token = token
    self.title = title
    self.file_path = file_path
    self.chunk_size = chunk_size

  def raw_issue_request(self, method, url, data=None, binary=False):
    headers = {'Authorization': 'token ' + self.token}
    if data is not None and not binary:
      data = json.dumps(data)
    response = requests.request(method, url, headers=headers, data=data)
    response.raise_for_status()
    try:
      result = json.loads(response.content)
    except ValueError:
      result = response.content

    return result

  def issue_request(self, method, endpoint, *args, **kwargs):
    return self.raw_issue_request(method, BASE_URL.format(endpoint=endpoint), *args, **kwargs)

  def list_articles(self):
    result = self.issue_request('GET', 'account/articles')
    print('Listing current articles:')
    if result:
      for item in result:
        print(u'  {url} - {title}'.format(**item))
    else:
      print('  No articles.')
    print('\n')

  def create_article(self):
    data = {
        # You may add any other information about the article here as you wish.
        'title': self.title
    }
    result = self.issue_request('POST', 'account/articles', data=data)
    print('Created article:', result['location'], '\n')

    result = self.raw_issue_request('GET', result['location'])

    return result['id']

  def list_files_of_article(self, article_id):
    result = self.issue_request(
        'GET', 'account/articles/{}/files'.format(article_id))
    print('Listing files for article {}:'.format(article_id))
    if result:
      for item in result:
        print('  {id} - {name}'.format(**item))
    else:
      print('  No files.')
    print('\n')

  def get_file_check_data(self, file_name):
    with open(file_name, 'rb') as fin:
      md5 = hashlib.md5()
      size = 0
      data = fin.read(self.chunk_size)
      while data:
        size += len(data)
        md5.update(data)
        data = fin.read(self.chunk_size)
      return md5.hexdigest(), size

  def initiate_new_upload(self, article_id, file_name):
    endpoint = 'account/articles/{}/files'
    endpoint = endpoint.format(article_id)

    md5, size = self.get_file_check_data(file_name)
    data = {'name': os.path.basename(file_name),
            'md5': md5,
            'size': size}

    result = self.issue_request('POST', endpoint, data=data)
    print('Initiated file upload:', result['location'], '\n')

    result = self.raw_issue_request('GET', result['location'])

    return result

  def complete_upload(self, article_id, file_id):
    self.issue_request(
        'POST', 'account/articles/{}/files/{}'.format(article_id, file_id))

  def upload_parts(self, file_info):
    url = '{upload_url}'.format(**file_info)
    result = self.raw_issue_request('GET', url)

    print('Uploading parts:')
    with open(self.file_path, 'rb') as fin:
      for part in result['parts']:
        self.upload_part(file_info, fin, part)
    print('\n')

  def upload_part(self, file_info, stream, part):
    udata = file_info.copy()
    udata.update(part)
    url = '{upload_url}/{partNo}'.format(**udata)

    stream.seek(part['startOffset'])
    data = stream.read(part['endOffset'] - part['startOffset'] + 1)

    self.raw_issue_request('PUT', url, data=data, binary=True)
    print(
        '  Uploaded part {partNo} from {startOffset} to {endOffset}'.format(**part))

  def upload_article(self):
    # We first create the article
    self.list_articles()
    # article_id = self.create_article()
    # self.list_articles()
    # self.list_files_of_article(article_id)

    # # Then we upload the file.
    # file_info = self.initiate_new_upload(article_id, self.file_path)
    # # Until here we used the figshare API; following lines use the figshare upload service API.
    # self.upload_parts(file_info)
    # # We return to the figshare API to complete the file upload process.
    # self.complete_upload(article_id, file_info['id'])
    # self.list_files_of_article(article_id)


def main(argv):
  del argv  # Unused.

  # print('Running under Python {0[0]}.{0[1]}.{0[2]}'.format(sys.version_info),
  #       file=sys.stderr)
  logging.info('Title is %s.', FLAGS.title)
  uploader = FishareUploader(FIGSHARE_TOKEN, FLAGS.title, FLAGS.file)
  uploader.upload_article()


if __name__ == '__main__':
  app.run(main)
