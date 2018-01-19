from nose.tools import eq_

from ..text_split import text_split


def test_simple_text_split():
    
    
    input = "As a sentence, this includes punctuation. \n" + \
            "\n" + \
            "And then we have another sentence here!"
    
    expected = ['As', ' ', 'a', ' ', 'sentence', ',', ' ', 'this', ' ',
                'includes', ' ', 'punctuation', '.', ' \n\n', 'And', ' ',
                'then', ' ', 'we', ' ', 'have', ' ', 'another', ' ', 'sentence',
                ' ', 'here', '!']
    
    tokens = list(text_split.tokenize(input))
    
    eq_(tokens, expected)
