import apache_beam as beam
import logging
import copy
import json
import tempfile
import resource
import os
import shutil
from google.cloud import storage

from construct_utils.conversation_constructor import Conversation_Constructor


class ReconstructConversation(beam.DoFn):
  def merge(self, ps1, ps2):
       # Merge two page states, ps1 is the later one
       deleted_ids_ps2 = {d[1]:d for d in ps2['deleted_comments']}
       deleted_ids_ps1 = {d[1]:d for d in ps1['deleted_comments']}
       deleted_ids_ps2.update(deleted_ids_ps1)
       extra_ids = [key for key in deleted_ids_ps2.keys() if key not in deleted_ids_ps1]
       ret_p = copy.deepcopy(ps1)
       ret_p['deleted_comments'] = list(deleted_ids_ps2.values())
       conv_ids = ps2['conversation_id']
       auth = ps2['authors']
       ret_p['conversation_id'] = ret_p['conversation_id']
       ret_p['authors'] = ret_p['authors']
       for i in extra_ids:
           ret_p['conversation_id'][i] = conv_ids[i]
           ret_p['authors'][i] = auth[i]
       ret_p['conversation_id'] = ret_p['conversation_id']
       ret_p['authors'] = ret_p['authors']
       return ret_p

  def process(self, info, tmp_input):
    """
    Args:
      bucket: a cloud storage bucket.
      tmp_input: a path to copy JSON revision files from. This
        allows data to be copied to this local machine's disk for external
        sorting (when there are more revisions than can fit in memory).
    """
    LOG_INTERVAL = 100
    # The max memory used in of this process KB, before warning are logged.
    MEMORY_THERESHOLD = 1000000

    (page_id, data) = info
    if (page_id == None): return
    logging.info('USERLOG: Reconstruction work start on page: %s' % page_id)
    # Load input from cloud
    last_revision = data['last_revision']
    page_state = data['page_state']
    error_log = data['error_log']
    # Clean type formatting
    if last_revision != []:
       assert(len(last_revision) == 1)
       last_revision = last_revision[0]
    else:
       last_revision = None
    if page_state != []:
       assert(len(page_state) == 1)
       page_state = page_state[0]
       page_state['page_state']['actions'] = \
           {int(pos) : tuple(val) for pos, val in page_state['page_state']['actions'].iteritems()}
       page_state['authors'] = \
           {action_id: [tuple(author) for author in authors] \
            for action_id, authors in page_state['authors'].iteritems()}
    else:
       page_state = None
    if error_log != []:
       assert(len(error_log) == 1)
       error_log = error_log[0]
    else:
       error_log = None
    rev_ids = []
    rev_ids = data['to_be_processed']
    # Return when the page doesn't have updates to be processed
    if len(rev_ids) == 0  or (error_log and
                              error_log['rev_id'] <= min(r['rev_id'] for r in rev_ids)):
       assert((last_revision and page_state) or \
              ((last_revision is None) and (page_state is None)))
       if last_revision:
          yield beam.pvalue.TaggedOutput('last_revision', json.dumps(last_revision))
          yield beam.pvalue.TaggedOutput('page_states', json.dumps(page_state))
       if error_log:
          yield beam.pvalue.TaggedOutput('error_log', json.dumps(error_log))
       logging.info('Page %s has no sufficient input in this time period.' % (page_id))
       return

    processor = Conversation_Constructor()
    if page_state:
       logging.info('Page %s existed: loading page state.' % (page_id))
       # Load previous page state.
       processor.load(page_state['deleted_comments'])
       latest_content = last_revision['text']
    else:
       latest_content = ""

    # Initialize
    last_revision_id = 'None'
    page_state_bak = None
    cnt = 0
    # Sort revisions by temporal order in memory.
    revision_lst = sorted(rev_ids, key=lambda x: (x['timestamp'], x['rev_id']))
    last_loading = 0
    logging.info('Reconstruction on page %s started.' % (page_id))
    if 'text' not in revision_lst[0]:
      tempfile_path = tempfile.mkdtemp()
      if tmp_input.startswith('gs://'):
        storage_client = storage.Client()
        bucket_name_end = tmp_input.find('/', 5)
        bucket = storage_client.get_bucket(tmp_input[5:bucket_name_end])
        prefix = os.path.join(tmp_input[bucket_name_end+1:], page_id)
        os.mkdir(tempfile_path, page_id)
        for blob in bucket.list_blobs(delimiter='/', prefix=prefix):
          suffix = os.path.basename(blob.name)
          blob.download_to_filename(os.path.join(tempfile_path, page_id, suffix))
      else:
        shutil.copytree(os.path.join(tmp_input, page_id),
                        os.path.join(tempfile_path, page_id))
    for key in revision_lst:
        if 'text' not in key:
           with open(os.path.join(tempfile_path, page_id, str(key['rev_id'])), 'r') as f:
              revision = json.load(f)
           os.remove(os.path.join(tempfile_path, page_id, str(key['rev_id'])))
        else:
           revision = key
        revision['rev_id'] = int(revision['rev_id'])
        # Process revision by revision.
        if 'rev_id' not in revision: continue
        cnt += 1
        last_revision_id = revision['rev_id']
        if revision['text'] == None: revision['text'] = ""
        logging.debug("REVISION CONTENT: %s" % revision['text'])
        try:
           page_state, actions, latest_content = \
               processor.process(page_state, latest_content, revision)
        except AssertionError:
           yield beam.pvalue.TaggedOutput('error_log', \
                      json.dumps({'page_id': page_id, 'rev_id': last_revision_id}))
           break

        for action in actions:
            yield json.dumps(action)
        memory_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if memory_used >= MEMORY_THERESHOLD:
          logging.warn("MEMORY USED MORE THAN THERESHOLD in PAGE %s REVISION %d : %d KB" %
            (revision['page_id'], revision['rev_id'], memory_used))
        if (cnt % LOG_INTERVAL == 0 and cnt) and page_state:
          # Reload after every LOG_INTERVAL revisions to keep the low memory
          # usage.
           processor = Conversation_Constructor()
           page_state_bak = copy.deepcopy(page_state)
           last_loading = cnt
           processor.load(page_state['deleted_comments'])
           page_state['deleted_comments'] = []
        revision = None
    if page_state_bak and cnt != last_loading:
       # Merge the last two page states if a reload happens while processing,
       # otherwise in a situation where a week's data contains LOG_INTERVAL + 1
       # revisions, the page state may only contain data from one revision.
       page_state = self.merge(page_state, page_state_bak)
    if error_log:
       yield beam.pvalue.TaggedOutput('error_log', json.dumps(error_log))
    yield beam.pvalue.TaggedOutput('page_states', json.dumps(page_state))
    yield beam.pvalue.TaggedOutput('last_revision', json.dumps(
      {'page_id': page_id, 'text': latest_content}))
    logging.info('USERLOG: Reconstruction on page %s complete! last revision: %s' %
      (page_id, last_revision_id))
