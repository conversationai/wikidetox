import json
import requests

THERESHOLD = 50 
FIELDS = 'blockinfo|groups|editcount|rights|registration|emailable|gender' 
SCHEMA = 'user_text|user_id|is_bot|is_admin|is_bureaucrat|blockinfo|editcount|registration|emailable|gender'.split('|')

def get_info(users):
    baseurl = 'http://en.wikipedia.org/w/api.php'
    my_atts = {}
    my_atts['action'] = 'query'  # action=query
    my_atts['format'] = 'json'
    my_atts['list'] = 'users'     # prop=info
    my_atts['ususers'] = '|'.join(users)   # format=json
    my_atts['usprop'] = FIELDS

    resp = requests.get(baseurl, params = my_atts)
    if not(resp.status_code == 200):
       with open("exceptions", "a") as e: 
            e.write(json.dumps(users) + '\n')
            e.write(resp.status_code)
       return []
    else:
       data = resp.json()['query']['users']
       ret = []
       for dat in data:
           cur = {}
           for s in SCHEMA: cur[s] = None
           cur.update({"user_text": dat['name']})
           for s in SCHEMA: 
               if s in dat:
                  cur[s] = dat[s]
           if 'groups' in dat:
              g = dat['groups']
              for group in ['bot', 'admin', 'bureaucrat']:
                  cur['is_%s'%group] = False
                  if group in g: cur['is_%s'%group] = True 
              if 'admins' in g or 'sysop' in g:
                 cur['is_admin'] = True
           if 'userid' in dat: 
              cur['user_id'] = dat['userid']
           if cur['gender'] == 'unknown':
              cur['gender'] = None
           ret.append(cur)
       return ret


users = []
progress = 0
total = 3602788
with open("user_info.json", "w") as w:
     with open("users.json", "r") as f:
          for line in f:
              data = json.loads(line)
              user = data['user_text']              
              progress += 1
              if progress <= 3345400:
                 continue
              users.append(user)
              if progress % 5000 == 0:
                 print("%d/%d finished"%(progress, total))
              if len(users) == THERESHOLD:
                 info = get_info(users)
                 for i in info:
                     w.write(json.dumps(i) + '\n')
                 users = []
          if len(users) > 0:
             info = get_info(users)
             for i in info:
                 w.write(json.dumps(i) + '\n')
 
           
