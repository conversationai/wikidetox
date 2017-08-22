import copy

def group_into_conversations(page_id, actions_lst):
    conversations = {}
    conv_mapping = {}
    for action in actions_lst:
        if action['type'] == 'COMMENT_ADDING' or action['type'] == 'COMMENT_MODIFICATION' \
           or action['type'] == 'SECTION_CREATION':
            if action['replyTo_id'] == None:
                conversations[action['id'] + '@' + page_id] = [action]
                conv_mapping[action['id']] = action['id'] + '@' + page_id
            else:
                conversations[conv_mapping[action['replyTo_id']]].append(action)
                conv_mapping[action['id']] = conv_mapping[action['replyTo_id']]
        if action['type'] == 'COMMENT_REMOVAL':
            conversations[conv_mapping[action['parent_id']]].append(action)
            conv_mapping[action['parent_id']]
        if action['type'] == 'COMMENT_RESTORATION':
            conversations[conv_mapping[action['parent_id']]].append(action)
            conv_mapping[action['id']] = conv_mapping[action['parent_id']]
    return conversations, conv_mapping

def update(snapshot, action):
    Found = False
    if action['type'] == 'COMMENT_REMOVAL':
        for ind, act in enumerate(snapshot):
            if action['parent_id'] in act['parent_ids']:
                act['status'] = 'removed'
                status = 'removed'
                snapshot[ind] = act
                Found = True
    if action['type'] == 'COMMENT_RESTORATION':
        for ind, act in enumerate(snapshot):
            if action['parent_id'] in act['parent_ids']:
                act['status'] = 'restored'
                act['content'] = action['content']
                status = 'restored'
                snapshot[ind] = act
                Found = True
    if action['type'] == 'COMMENT_MODIFICATION':
        found = False
        for i, act in enumerate(snapshot):
            if action['parent_id'] in act['parent_ids']:
                found = True
                pids = act['parent_ids']
                act = copy.deepcopy(action)
                act['parent_ids'] = pids
                act['status'] = 'content changed'
                status = 'content changed'
                act['relative_replyTo'] = -1
                act['parent_ids'][action['id']] = True
                for ind, a in enumerate(snapshot):
                    if a['id'] == action['replyTo_id']:
                        act['relative_replyTo'] = ind
                snapshot[i] = act
                Found = True
        if not(found):
            act = copy.deepcopy(action)
            act['status'] = 'just added'
            status = 'just added'
            act['relative_replyTo'] = -1
            for ind, a in enumerate(snapshot):
                if a['id'] == action['replyTo_id']:
                    act['relative_replyTo'] = ind
            act['parent_ids'] = {action['id'] : True}
            snapshot.append(act)
            Found = True
    if action['type'] == 'COMMENT_ADDING' or action['type'] == 'SECTION_CREATION':
        act = copy.deepcopy(action)
        act['status'] = 'just added'
        status = 'just added'
        act['relative_replyTo'] = -1
        Found = True
        for ind, a in enumerate(snapshot):
            if a['id'] == action['replyTo_id']:
                act['relative_replyTo'] = ind
        act['parent_ids'] = {action['id'] : True}
        snapshot.append(act)
    if not(Found): print(action)
    return snapshot, status

def display(snapshot):
    print('======================SNAPSHOT=============================')
    for ind, act in enumerate(snapshot):
        print('ID:%d\nREVID:%s\nCONTENT:%s\nAUTHOR:%s\nTIMESTAMP:%s\nSTATUS:%s\nREPLY TO:%d\nREPLY TO ID:%s' \
              %(ind, act['id'], act['content'], act['user_text'], act['timestamp'], act['status'], act['relative_replyTo'], act['replyTo_id']))
        print('LINK:https://en.wikipedia.org/w/index.php?diff=prev&oldid=%s'%(act['id'].split('.')[0]))
        print('---------------------------------------------------')
    print('===================================================')


def generate_snapshots(conv):
    snapshots = []
    snapshot = []
    displayed = False
    for action in conv:
        snapshot,status = update(snapshot, action)
        if status == 'just added':
            snapshots.append(copy.deepcopy(snapshot))
            displayed = True
        else:
            displayed = False
    if not(displayed):
        snapshots.append(copy.deepcopy(snapshot))
    return(snapshots)
