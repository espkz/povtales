# Author: Ellie Paek
# Last updated: [02/16/2023]

# Description: Telling the story of Snow White from the prince's point of view
# This might be super short because he doesn't appear until the end of the story lmaooo

from emora_stdm import DialogueFlow
from povtales.utils import *

prince_introductions = {
    'state': 'start',
    "`Hello there, nice to meet you! I am the Prince.`" : {
        '#ERR' : {
            "`Would you care to listen to my story about my wife?`" : {
                AGREE : {
                    "`Wonderful.`" : 'end'
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


prince = DialogueFlow('start', end_state='end')
prince.load_transitions(prince_introductions)

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