from nose.tools import eq_

from ..wikitext_split import wikitext_split


def test_wikitext_split():

    input = "As a sentence, this 34 includes punctuation. \n" + \
            "\n" + \
            "==Header!==\n" + \
            "मादरचोद मादरचोद " + \
            "مُنیر " + \
            "克·科伊尔 し〤。foobar!" + \
            "And then we have another sentence here!\n" + \
            "[//google.com foo] " + \
            "https://website.gov?param=value\n" + \
            "peoples' ain't d’encyclopédie\n" + \
            "<ref>derp</ref><ref name=\"foo\" />" + \
            "[[foo|bar]]" + \
            "mailto:email@email.mail " + \
            "위키백과의 운영은 비영리 단체인 위키미디어 재단이 " + \
            "দেখার পর তিনি চ্চিত্র " + \
            "'''some bold''' text m80"

    expected = [('As', 'word'),
                (' ', 'whitespace'),
                ('a', 'word'),
                (' ', 'whitespace'),
                ('sentence', 'word'),
                (',', 'comma'),
                (' ', 'whitespace'),
                ('this', 'word'),
                (' ', 'whitespace'),
                ('34', 'number'),
                (' ', 'whitespace'),
                ('includes', 'word'),
                (' ', 'whitespace'),
                ('punctuation', 'word'),
                ('.', 'period'),
                (' ', 'whitespace'),
                ('\n\n', 'break'),
                ('==', 'equals'),
                ('Header', 'word'),
                ('!', 'epoint'),
                ('==', 'equals'),
                ('\n', 'whitespace'),
                ('मादरचोद', 'word'),
                (' ', 'whitespace'),
                ('मादरचोद', 'word'),
                (' ', 'whitespace'),
                ('مُنیر', 'word'),
                (' ', 'whitespace'),
                ('克', 'cjk'),
                ('·', 'etc'),
                ('科', 'cjk'),
                ('伊', 'cjk'),
                ('尔', 'cjk'),
                (' ', 'whitespace'),
                ('し', 'cjk'),
                ('〤', 'japan_punct'),
                ('。', 'japan_punct'),
                ('foobar', 'word'),
                ('!', 'epoint'),
                ('And', 'word'),
                (' ', 'whitespace'),
                ('then', 'word'),
                (' ', 'whitespace'),
                ('we', 'word'),
                (' ', 'whitespace'),
                ('have', 'word'),
                (' ', 'whitespace'),
                ('another', 'word'),
                (' ', 'whitespace'),
                ('sentence', 'word'),
                (' ', 'whitespace'),
                ('here', 'word'),
                ('!', 'epoint'),
                ('\n', 'whitespace'),
                ('[', 'brack_open'),
                ('//google.com', 'url'),
                (' ', 'whitespace'),
                ('foo', 'word'),
                (']', 'brack_close'),
                (' ', 'whitespace'),
                ('https://website.gov?param=value', 'url'),
                ('\n', 'whitespace'),
                ('peoples\'', 'word'),
                (' ', 'whitespace'),
                ('ain\'t', 'word'),
                (' ', 'whitespace'),
                ('d’encyclopédie', 'word'),
                ('\n', 'whitespace'),
                ('<ref>', 'ref_open'),
                ('derp', 'word'),
                ('</ref>', 'ref_close'),
                ('<ref name="foo" />', 'ref_singleton'),
                ('[[', 'dbrack_open'),
                ('foo', 'word'),
                ('|', 'bar'),
                ('bar', 'word'),
                (']]', 'dbrack_close'),
                ('mailto:email@email.mail', 'url'),
                (' ', 'whitespace'),
                ('위키백과의', 'word'),
                (' ', 'whitespace'),
                ('운영은', 'word'),
                (' ', 'whitespace'),
                ('비영리', 'word'),
                (' ', 'whitespace'),
                ('단체인', 'word'),
                (' ', 'whitespace'),
                ('위키미디어', 'word'),
                (' ', 'whitespace'),
                ('재단이', 'word'),
                (' ', 'whitespace'),
                ('দেখার', 'word'),
                (' ', 'whitespace'),
                ('পর', 'word'),
                (' ', 'whitespace'),
                ('তিনি', 'word'),
                (' ', 'whitespace'),
                ('চ্চিত্র', 'word'),
                (' ', 'whitespace'),
                ("'''", 'bold'),
                ('some', 'word'),
                (' ', 'whitespace'),
                ('bold', 'word'),
                ("'''", 'bold'),
                (' ', 'whitespace'),
                ('text', 'word'),
                (' ', 'whitespace'),
                ('m80', 'word')]

    tokens = list(wikitext_split.tokenize(input))

    for token, (s, t) in zip(tokens, expected):
        print(repr(token), (s, t))
        eq_(token, s)
        eq_(token.type, t)


def test_arabic():
    input = "يرجع الأمويون في نسبهم إلى أميَّة بن عبد شمس من قبيلة قريش."
    expected = [("يرجع", "word"),
                (" ", "whitespace"),
                ("الأمويون", "word"),
                (" ", "whitespace"),
                ("في", "word"),
                (" ", "whitespace"),
                ("نسبهم", "word"),
                (" ", "whitespace"),
                ("إلى", "word"),
                (" ", "whitespace"),
                ("أميَّة", "word"),
                (" ", "whitespace"),
                ("بن", "word"),
                (" ", "whitespace"),
                ("عبد", "word"),
                (" ", "whitespace"),
                ("شمس", "word"),
                (" ", "whitespace"),
                ("من", "word"),
                (" ", "whitespace"),
                ("قبيلة", "word"),
                (" ", "whitespace"),
                ("قريش", "word"),
                (".", "period")]

    tokens = list(wikitext_split.tokenize(input))

    for token, (s, t) in zip(tokens, expected):
        print(repr(token), (s, t))
        eq_(token, s)
        eq_(token.type, t)


def test_hebrew():
    input = 'דגל קנדה הידוע בכינויו "דגל עלה האדר" (או המייפל) אומץ בשנת ' + \
            '1965 לאחר דיון ציבורי סביב שאלת הסמלים הלאומיים שבו.'

    expected = [("דגל", "word"),
                (" ", "whitespace"),
                ("קנדה", "word"),
                (" ", "whitespace"),
                ("הידוע", "word"),
                (" ", "whitespace"),
                ("בכינויו", "word"),
                (" ", "whitespace"),
                ('"', "etc"),
                ("דגל", "word"),
                (" ", "whitespace"),
                ("עלה", "word"),
                (" ", "whitespace"),
                ("האדר", "word"),
                ('"', "etc"),
                (" ", "whitespace"),
                ('(', "paren_open"),
                ("או", "word"),
                (" ", "whitespace"),
                ("המייפל", "word"),
                (")", "paren_close"),
                (" ", "whitespace"),
                ("אומץ", "word"),
                (" ", "whitespace"),
                ("בשנת", "word"),
                (" ", "whitespace"),
                ("1965", "number"),
                (" ", "whitespace"),
                ("לאחר", "word"),
                (" ", "whitespace"),
                ("דיון", "word"),
                (" ", "whitespace"),
                ("ציבורי", "word"),
                (" ", "whitespace"),
                ("סביב", "word"),
                (" ", "whitespace"),
                ("שאלת", "word"),
                (" ", "whitespace"),
                ("הסמלים", "word"),
                (" ", "whitespace"),
                ("הלאומיים", "word"),
                (" ", "whitespace"),
                ("שבו", "word"),
                (".", "period")]

    tokens = list(wikitext_split.tokenize(input))

    for token, (s, t) in zip(tokens, expected):
        print(repr(token), (s, t))
        eq_(token, s)
        eq_(token.type, t)


def test_hindi():
    input = 'वसा अर्थात चिकनाई शरीर को क्रियाशील बनाए रखने मे सहयोग करती है।'

    expected = [("वसा", "word"),
                (" ", "whitespace"),
                ("अर्थात", "word"),
                (" ", "whitespace"),
                ("चिकनाई", "word"),
                (" ", "whitespace"),
                ("शरीर", "word"),
                (" ", "whitespace"),
                ("को", "word"),
                (" ", "whitespace"),
                ("क्रियाशील", "word"),
                (" ", "whitespace"),
                ("बनाए", "word"),
                (" ", "whitespace"),
                ("रखने", "word"),
                (" ", "whitespace"),
                ("मे", "word"),
                (" ", "whitespace"),
                ("सहयोग", "word"),
                (" ", "whitespace"),
                ("करती", "word"),
                (" ", "whitespace"),
                ("है", "word"),
                ("।", "danda")]

    tokens = list(wikitext_split.tokenize(input))

    for token, (s, t) in zip(tokens, expected):
        print(repr(token), (s, t))
        eq_(token, s)
        eq_(token.type, t)
