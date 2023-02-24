# Author: Ellie Paek
# Last updated: [02/24/2023]

# Description: Telling the story of Snow White from the prince's point of view
# This might be super short because he doesn't appear until the end of the story lmaooo
# Dr. Choi said 20 words or less per conversation which makes sense but also,,, h

# To Do:
# connect stories to elsewhere (global??)
# end module
# what if someone comes back after talking to another character? would there be a save point?

from emora_stdm import DialogueFlow
from utils.general_utils import *

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

prince_story_beginning = {
    'state' : 'prince_beginning',
    "`It all started when I was on horseback, strolling through the forest, when I came upon an old cottage.`" : {
        '[{dwarf, dwarves, snow white}]' : {
            "`Yes, that's right! That was where they were living.`" : 'meet_dwarves'
        },
        '#ERR' : {
            'state' : 'meet_dwarves',
            "`It was also getting dark, so I went to the house to ask for a place to rest for the night. The cottage was owned by seven dwarves, who thankfully accepted me to stay, but looked very sad.`" : {
                '[why, sad]' : {
                    "`I was wondering the same thing!`" : 'prince_middle'
                },
                '#ERR' : {
                    "`Yes, anyway, I was wondering why they looked so sad`" : 'prince_middle'
                }
            }
        }
    }
}

prince_story_middle = {
    'state' : 'prince_middle',
    "`When I asked them, \"Why do look so sad?\" and they looked at a mountain. When I looked at it too, I saw a glass coffin at the top.`" : {
        '#ERR' : {
            "`When I went up the mountain, there was the most beautiful woman inside of the coffin. On the outside was written, \'Princess Snow White.\'`" : {
                '#ERR' : {
                    "`Snow White inside the coffin was so beautiful, I asked the dwarves if I can have the coffin. They said no at first, but I promised I would take care of her.`" : {
                        '#ERR' : {
                            "`Finally, they agreed, and I was able to take the coffin with me.`" : {
                                '#ERR' : 'prince_end'
                            }
                        }
                    }
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

prince_story_end = {
    'state' : 'prince_end',
    "`While carrying the coffin back, Snow White awoke! It was a miracle!`" : {
        '#ERR' : {
            "`She was even more beautiful alive, and I immediately confessed my love to her, and asked her to marry me.`" : {
                '#ERR' : {
                    "`And she said yes! We went back to my castle, and had a grand wedding. And now, we're still together, living happily ever after.`" : {
                        '#ERR' : 'outro'
                    }
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

prince_outro = {
    'state' : 'outro',
    "`Well, thank you for listening to my story. Would you like to speak to anyone else?`" : {
        AGREE : {
            "`Who would you like to speak to?`" : {
                '#ERR' : {
                    "`Very well. I hope to see you soon.`" : 'end' # end for now
                }
            }
        },
        DISAGREE: {
            "`Alright.`" : 'ending'
        },
        '#ERR' : {
            'state' : 'ending',
            "`Well, I hope to speak to you soon. Farewell!`" : 'end'
        }
    }
}


prince = DialogueFlow('start', end_state='end')
prince.load_transitions(prince_introductions)
prince.load_transitions(prince_story_beginning)
prince.load_transitions(prince_story_middle)
prince.load_transitions(prince_story_end)
prince.load_transitions(prince_outro)

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