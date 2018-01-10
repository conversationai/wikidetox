from deltas.tokenizers import text_split
from rev_clean import clean
from diff import diff_tuning

from deltas.algorithms import sequence_matcher

def convert_diff_format(x, a, b):
    ret = {}
    ret['name'] = x.name
    ret['a1'] = x.a1
    ret['a2'] = x.a2
    ret['b1'] = x.b1
    ret['b2'] = x.b2
    if x.name == 'insert':
       ret['tokens'] = b[x.b1:x.b2]
    if x.name == 'delete':
       ret['tokens'] = a[x.a1:x.a2]
    return ret
rev1="{{WPBiography|living=no|class=start|priority=mid}}\n== release date ==\n\n\ni changed the release year of \"A Dirty War: A Russian reporter in Chechnya\" from 1999 to 2003, source: the book --[[User:Dox|Dox]] 13:51, 18 August 2006 (UTC)\n----\n\n== Assassination ==\nThe article claims that she presented Chechen rebels in a \"flattering\" light.  However, the NY Times & the BBC do not mention this & the Economist notes that she interviewed the mothers of fallen Russian soldiers in Chechnya as well as the families of disappeared Chechens.  Does anyone know of a good site to research this further?\n\nis it possible that someone close to the government was so stupid to kill her, right now that previous attempt failed and were denounced, thus risking international isolation and despise? or is it a foreign attempt to discredit Putin's rule and mount another \"orange revolution\" against him?\n-- You can take a part in these discussions all over the runet, there's no point trying to talk about that in wikipedia. --[[User:GolerGkA|GolerGkA]] 21:52, 7 October 2006 (UTC)\n\nAnd as for whether its is possible... yes, but unlikely because Russia is trying to join the WTO. And if you think someone who don't want Russia to join the WTO killed her, you are a conspiracy theorist.  Anyways this is not the place to talke about this. [[User:Pseudoanonymous|Pseudoanonymous]] 01:18, 8 October 2006 (UTC)\n:Er, conspiracy theory or not, you deigned to comment on it yourself. She riled enough people in the country that anti-WTO parties with grudges themselves would just be in with the rest of the wash of complaints against her."
rev2="{{WPBiography|living=no|class=start|priority=mid}}\n== release date ==\n\n\ni changed the release year of \"A Dirty War: A Russian reporter in Chechnya\" from 1999 to 2003, source: the book --[[User:Dox|Dox]] 13:51, 18 August 2006 (UTC)\n----\n\n== Assassination ==\n\nis it possible that someone close to the government was so stupid to kill her, right now that previous attempt failed and were denounced, thus risking international isolation and despise? or is it a foreign attempt to discredit Putin's rule and mount another \"orange revolution\" against him?\n-- You can take a part in these discussions all over the runet, there's no point trying to talk about that in wikipedia. --[[User:GolerGkA|GolerGkA]] 21:52, 7 October 2006 (UTC)\n\nAnd as for whether its is possible... yes, but unlikely because Russia is trying to join the WTO. And if you think someone who don't want Russia to join the WTO killed her, you are a conspiracy theorist.  Anyways this is not the place to talke about this. [[User:Pseudoanonymous|Pseudoanonymous]] 01:18, 8 October 2006 (UTC)\n:Er, conspiracy theory or not, you deigned to comment on it yourself. She riled enough people in the country that anti-WTO parties with grudges themselves would just be in with the rest of the wash of complaints against her."

a = text_split.tokenize(clean(rev1))
b = text_split.tokenize(clean(rev2))
print(clean(rev1))
print('=============================SEPERATION==============================')
print(clean(rev2))

        
diffs = sorted([convert_diff_format(x, a, b) for x in list(sequence_matcher.diff(a, b))], key=lambda k: k['a1'])
for op in diffs:
   print(op['name'], op['a1'], op['a2'], op['b1'], op['b2'])

diffs = diff_tuning(diffs, a, b)
diffs = sorted(diffs, key=lambda k: k['a1']) 
for op in diffs:
   print(op['name'], op['a1'], op['a2'], op['b1'], op['b2'])
   if 'tokens' in op: print(''.join(op['tokens']))



