import requests
import json
import os

def query_with_end(title, end):
    request = {}
    request['action'] = 'query'
    request['format'] = 'json'
    request['prop'] = 'revisions'
    request['titles'] = title
    request['rvprop'] = 'ids|timestamp|user|content|userid|sha1'
    request['rvlimit'] = 'max'
    request['rvstartid'] = end
    revs = []
    lastContinue = {}
    while True:
        # Clone original request
        req = request.copy()
        # Modify it with the values returned in the 'continue' section of the last result.
        # Call API
        result = requests.get('http://en.wikipedia.org/w/api.php', params=req).json()
        if 'error' in result:
            raise Error(result['error'])
        if 'warnings' in result:
            print(result['warnings'])
        if 'query' in result:
            p = list(result['query']['pages'].keys())[0]
            return result['query']['pages'][p]['revisions'], p, result['query']['pages'][p]['ns']
        if 'rvcontinue' not in result:
            break
        request['rvcontinue'] = result['continue']

def get_revisions(title, end = '773232766', output_dir = 'json_dumps'):
    ret = []
    page_id = 0
    while True:
        ans, page_id, ns = query_with_end(title, end)
        if ret == []:
            ret = ans
        else:
            for x in ans[1:]:
                ret.append(x)
        if not(len(ans) < 50):
            end = ans[-1]['revid']
        else:
            break
    revlist = []
    ret = ret[::-1]
    for x in ret:
        x['text'] = x['*']
        x['page_id'] = page_id
        x['page_title'] = title
        x['user_id'] = x['userid']
        x['user_text'] = x['user']
        x['rev_id'] = x['revid']
        del x['*']
        del x['user']
        del x['userid']
        del x['revid']
    filename = '%s_%s_%s.json' % (page_id, title, ns)
    with open(os.path.join(output_dir, filename), 'w') as w:
        json.dump(ret, w)
    return ns, ret
