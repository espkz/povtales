#Common NLU, also yoinked from Emora chatbot

AGREE = '-{not} [{' \
        'sure, i know, i do, i am, ok, okay, okie, ye, ' \
        'yes, yeah, yea, yah, yep, yup, think so, i know, absolutely, exactly, correct, precisely, ' \
        'certainly, surely, definitely, probably, totally, true, of course, right, agree, agreed' \
        '}]'

DISAGREE = '-{know}, {' + ', '.join([
    '[{no, nay, nah, na, not really, nope, no way, wrong}]',
    '[{absolutely, surely, definitely, certainly, i think} not]',
    '[i, am, not]',
    '[i do not]',
    '[not true]',
    '[!i, am, good]'
]) + '}'

DONT_KNOW = '[{' \
            'idk, meh, eh, blah,' \
            'dont know, dunno, do not know, unsure, indifferent, [not, {sure,certain}], hard to say, no idea, uncertain, ' \
            '[!no {opinion, opinions, idea, ideas, thought, thoughts, knowledge}],' \
            '[{not}, have, {opinion, opinions, idea, ideas, thought, thoughts, knowledge}],' \
            '[!{not} {think, remember, recall, decide, sure}]' \
            '}]'

MAYBE = '[{maybe, possibly, sort of, kind of, kinda, a little, at times, sometimes, could be, potentially, [it, possible]}]'

SATISFIED = AGREE + '-{not} [{perfect, good, wonderful, great, awesome, thank, thanks, exactly, exact, helpful}]'

ME_TOO = '{[{me, i, mine}, {also, too, neither}], [!so {am, do, did} i], [same]}'

FEELING_BAD = '-{not} [{bad, badly, terrible, terribly, mess, sucks, sucked, hard, horrible, horribly, awful, tough, frustrated, frustrating, stressed, stressful, managing poorly, managing badly, poorly, overwhelmed, sleep deprived, tired, meh, blah, sucks, struggle, struggling, sad, rough, failure, fail, hate, hopeless, depressed}]'

FEELING_BAD_2 ='[not, {good, great, well, happy, ok, okay}]'

JOKE = '[{joke, joking, expression, phrase, term, kidding}]'

APOLOGY = '[{sorry, sry, my bad, apologize, apologies, oops, whoops}]'

ASK_WHY = '[{how come, why, [{why, how come}, {you, you are, your, are you}]}]'

DISLIKE = '[{stupid, dumb, lame, boring, weird, hate, dislike, gross, not like, not love, sucks, sucked, annoying, annoy, annoyed}]'

WHAT_ABOUT_YOU = '{[{what, how}, about, {you, your}], [wby], [wbu], [hbu], [what, your, {fav, fave, favorite}]}'

FUNNY = '[{ha, haha, hahaha, fun, funny, lol, comedy, comedian, pun, lmao, [{good, nice} {joke, one}]}]'