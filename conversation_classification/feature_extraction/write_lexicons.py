import json

lexicon = {
    'pron_me': ['i', "i'd", "i'll", "i'm", "i've", 'id', 'im', 'ive',
                'me', 'mine', 'my', 'myself'],
    'pron_we': ["let's", 'lets', 'our', 'ours', 'ourselves', 'us',
                'we', "we'd", "we'll", "we're", "we've", 'weve'],
    'pron_you': ["y'all", 'yall', 'you', "you'd", "you'll", "you're",
                 "you've", 'youd', 'youll', 'your', 'youre', 'yours',
                 'youve'],
    'pron_3rd': ['he', "he'd", "he's", 'hed', 'her', 'hers', 'herself',
                 'hes', 'him', 'himself', 'his', 'she', "she'd",
                 "she'll", "she's", 'shes'],
    'pron_3rd_plural': ['their', 'them', 'themselves',
                 'they', "they'd", "they'll", "they've", 'theyd', 'theyll',
                 'theyve', "they're", "theyre"]
}

lexicon['positive'] = []
with open('liu-positive-words.txt') as f:
     for line in f:
         lexicon['positive'].append(line.strip()) 
lexicon['negative'] = []
with open('liu-negative-words.txt', encoding='ISO-8859-1') as f:
     for line in f:
         lexicon['negative'].append(line.strip())
with open('lexicons', 'w') as w:
    json.dump(lexicon, w)
