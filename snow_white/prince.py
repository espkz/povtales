# Author: Ellie Paek
# Last updated: [02/23/2023]

# Description: Telling the story of Snow White from the prince's point of view
# This might be super short because he doesn't appear until the end of the story lmaooo

from emora_stdm import DialogueFlow
from utils.macro_utils import *

prince_introductions = {
    'state': 'start',
    "`Hello there, nice to meet you! I am the Prince.`" : {
        '#ERR' : {
            "`Would you care to listen to my story about my wife?`" : {
                AGREE : {
                    "`Wonderful.`" : 'prince_beginning'
                },
                DISAGREE : 'rejected',
                '#ERR' : {
                    'state' : 'rejected',
                    "`Very well, do let me know if you would like to listen to it.`" : 'end'
                }
            }
        }
    },
    "` `": {
        # error catch moving onto the next topic
        'score': 0,
        'state': 'SYSTEM:start'
    }
}

prince_story = {
    'state' : 'prince_beginning',
    "`I met my wife while I was taking a stroll through the woods. I was on horseback, enjoying the beautiful view of the forest, when I came up an old cottage in the middle of it.`" : {
        '[{dwarf, dwarves, snow white}]' : {
            "`Yes, that's right! That was where they were living.`" : 'encounter_with_coffin'
        },
        '#ERR' : {
            'state' : 'encounter_with_coffin',
            "`And so this sudden house in the middle of the woods interested me. Who could possibly be living in the middle of these quiet woods? It was also getting quite dark, and I longed for a place to rest, so I approached the house to seek shelter for the night. The cottage was owned by seven dwarves, who thankfully accepted me to stay, yet had such sad expressions on their faces.`" : {
                '[why, sad]' : 'end',
                '#ERR' : 'end'
            }
        }
    }
}


prince = DialogueFlow('start', end_state='end')
prince.load_transitions(prince_introductions)
prince.load_transitions(prince_story)

if __name__ == '__main__':
    prince.add_macros({
        'G': VAR_GATE(),
        'ANY_GATE': ANY_GATE(),
        'OPEN_G': OPEN_G(),
        'CLOSE_G': CLOSE_G(),
        'NORMALIZE': NORMALIZE(),
        'ERR': Error()
    })
    prince.load_update_rules({
        '#NORMALIZE': None  # Always expands the contractions of what the user says
    })
    prince.precache_transitions()
    prince.run(debugging=False)