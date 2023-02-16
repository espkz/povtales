# Author: Ellie Paek
# Last updated: [10/23/2022] — additional fixes, options added

# Description: test

from emora_stdm import DialogueFlow


test_transitions = {
    'state': 'start',
    "`Hi! Nice to meet you.`" : {
        'error' : 'end'
    },
    "` `": {
        # error catch moving onto the next topic
        'score': 0,
        'state': 'SYSTEM:start'
    }
}

# This is the DialogueFlow object that will be imported as a component of Big Emora
test = DialogueFlow('start', end_state='end')
test.load_transitions(test_transitions)


if __name__ == '__main__':
    test.run(debugging=False)