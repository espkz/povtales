# macros and NLU yoinking from Emora companion bot

import operator as _operator
import random
import contractions
import os
import time
from datetime import datetime as dt

from emora_stdm import Macro, CompositeDialogueFlow

# This serves as normalization for the NLG
class CompositeDialogueFlow2(CompositeDialogueFlow):
    def system_turn(self, debugging=False):
        raw_response = super().system_turn(debugging)
        # Replace double spaces with one space and strip whitespace from beginnings and end
        fixed_response = raw_response.strip()
        fixed_response = fixed_response.replace(" ,", ",") # internal spaces
        fixed_response = fixed_response.replace(" .", ".")
        fixed_response = fixed_response.replace(" !", "!")
        fixed_response = fixed_response.replace(" ?", "?")
        for i in range(0,3):
            fixed_response = fixed_response.replace("  ", " ")

        if fixed_response == ' ' or fixed_response == '':  # empty string. Better than saying nothing...
            name = self.controller().vars().get('user_name', "")
            if name != "":
                name = name.capitalize()
            else:
                name = "friend"
            fixed_response = "I think you're pretty cool, " + name + ". I'm having a good time chatting so far!"
        self.controller().vars()['__raw_sys_utterance__'] = fixed_response
        return fixed_response


def filepath(relative_path):
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
    return os.path.join(__location__, relative_path)


class VAR_GATE(Macro):
    def run(self, ngrams, vars, args):
        gates = vars.setdefault('__var_gates__', {})
        closed = False
        for flag in args:
            if gates.get(flag):
                closed = True
            gates[flag] = True
        opened = not closed
        return opened

# If any gate in args is open, then ANY_GATE returns True. ("OR" operator)
class ANY_GATE(Macro):
    def run(self, ngrams, vars, args):
        gates = vars.setdefault('__var_gates__', {})
        args = set(args)
        at_least_one_open = False
        for arg_name in args:
            if not gates.get(arg_name):
                at_least_one_open = True
        # for gate_name, closed in gates.items():
        #     if gate_name in args and not closed:
        #         at_least_one_open = True
        return at_least_one_open

# 11/29/22 open the specified gates
class OPEN_G(Macro):
    def run(self, ngrams, vars, args):
        gates = vars.setdefault('__var_gates__', {})
        args = set(args)
        for arg_name in args:
            if gates.get(arg_name):
                gates[arg_name] = False
        return True

# Close the specified gates.
class CLOSE_G(Macro):
    def run(self, ngrams, vars, args):
        gates = vars.setdefault('__var_gates__', {})
        args = set(args)
        for arg_name in args:
            gates[arg_name] = True
        return True

_comparisons = {
    '<=': _operator.le,
    '>=': _operator.ge,
    '!=': _operator.ne,
    '<': _operator.lt,
    '>': _operator.gt,
    '==': _operator.eq,
    # '=': _operator.eq
}


def _update_gate(vars, args):
    gates = {a for a in args if not any((c in a for c in '<>='))}
    for arg in set(args) - gates:
        close = False
        for expression in [expression.strip() for expression in arg.split("||")]:
            for c in _comparisons:
                if c in expression:
                    sides = [side.strip() for side in expression.split(c)]
                    for i, side in enumerate(sides):
                        if side.isnumeric():
                            sides[i] = float(side)
                        elif side == 'True':
                            sides[i] = True
                        elif side == 'False':
                            sides[i] = False
                        else:
                            sides[i] = vars.get(side)
                    # If the variable isn't set we just always close the gate.
                    if None in sides or not _comparisons[c](*sides):
                        close = True
        # If the variable isn't set we just always close the gate.
        if close:
            gate_vars = vars.setdefault('__var_gates__', {})
            for gate in gates:
                gate_vars[gate] = True
            return


class UPDATE_GATE(Macro):
    def run(self, ngrams, vars, args):
        _update_gate(vars, args)
        return True


class BATCH_UPDATE_GATES(Macro):

    def __init__(self, update_dict):
        Macro.__init__(self)
        self.updates = update_dict

    def run(self, ngrams, vars, args):
        for conditions, gates in self.updates.items():
            if not isinstance(conditions, tuple):
                conditions = (conditions,)
            if not isinstance(gates, tuple):
                gates = (gates,)
            _update_gate(vars, (*gates, *conditions))
        return True


class NORMALIZE(Macro):
    def run(self, ngrams, vars, args):
        text = ngrams.text()

        # truncation, to avoid catastrophic regex match slowdown
        words = text.split()
        num_words = len(words)
        num_chars = len(text)
        if num_words > 12:
            text = ' '.join(words[:6]) + ' ' + ' '.join(words[-6:])
        elif num_chars > 200:
            text =  text[:100] + text[-100:]

        #expanded_user_utterance = text.replace(" ur ", " your ")
        expanded_user_utterance = text.replace(" u ", " you ")
        expanded_user_utterance = expanded_user_utterance.replace("wby", "what about you")

        expanded_user_utterance = contractions.fix(expanded_user_utterance) # expand contractions and some abbreviations like tbh
        expanded_user_utterance = expanded_user_utterance.replace("cannot", "can not") # expand contractions

        # expanded_user_utterance = spell(expanded_user_utterance)  #Autocorrect

        expanded_user_utterance = ''.join([c.lower() for c in expanded_user_utterance if c.isalnum() or c == ' ']) # make lowercase, strip all punctuation
        expanded_user_utterance = expanded_user_utterance.strip() # get rid of pesky extra spaces

        if expanded_user_utterance != vars.get('__raw_user_utterance__'):
            vars['__raw_user_utterance__'] = text

        vars['__user_utterance__'] = expanded_user_utterance
        return True

class NON_ENGLISH(Macro):
    def run(self, ngrams, vars, args):
        text = ngrams.text()
        return not text.isascii()
        # True if there are any non-ascii characters, that are not English.

class Error(Macro):
    def run(self, ngrams, vars, args):
        vars['__score__'] = 0
        return True