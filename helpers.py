#!/usr/bin/env python3

import re
from collections import OrderedDict
from functools import partial

def flatten(l):
    # flatten list of lists by 1
    return [item for sublist in l for item in sublist]

def unique(l):
    # unique items in a list
    return list(set(l))

def remove_empty(mylist):
    return [l for l in mylist if l]

def hasNumbers(inputString):
    return bool(re.search(r'\d', inputString))

# https://stackoverflow.com/questions/45128959/python-replace-multiple-strings-while-supporting-backreferences

def multiple_replace(text, repldict):
    # split the dict into two lists because we need the order to be reliable
    keys, repls = zip(*repldict.items())

    # generate a regex pattern from the keys, putting each key in a named group
    # so that we can find out which one of them matched.
    # groups are named "_<idx>" where <idx> is the index of the corresponding
    # replacement text in the list above
    pattern = '|'.join('(?P<_{}>{})'.format(i, k) for i, k in enumerate(keys))

    def repl(match):
        # find out which key matched. We know that exactly one of the keys has
        # matched, so it's the only named group with a value other than None.
        group_name = next(name for name, value in match.groupdict().items()
                          if value is not None)
        group_index = int(group_name[1:])

        # now that we know which group matched, we can retrieve the
        # corresponding replacement text
        repl_text = repls[group_index]

        # now we'll manually search for backreferences in the
        # replacement text and substitute them
        def repl_backreference(m):
            reference_index = int(m.group(1))

            # return the corresponding group's value from the original match
            # +1 because regex starts counting at 1
            return match.group(group_index + reference_index + 1)  

        return re.sub(r'\\(\d+)', repl_backreference, repl_text)

    return re.sub(pattern, repl, text)

# https://stackoverflow.com/questions/45128959/python-replace-multiple-strings-while-supporting-backreferences
#https://stackoverflow.com/questions/6116978/how-to-replace-multiple-substrings-of-a-string

def build_replacer(cases):
    ordered_cases = OrderedDict(cases.items())
    replacements = {}

    leading_groups = 0
    for pattern, replacement in ordered_cases.items():
        leading_groups += 1

        # leading_groups is now the absolute position of the root group (back-references should be relative to this)
        group_index = leading_groups
        replacement = absolute_backreference(replacement, group_index)
        replacements[group_index] = replacement

        # This pattern contains N subgroups (determine by compiling pattern)
        subgroups = re.compile(pattern).groups
        leading_groups += subgroups

    catch_all = "|".join("({})".format(p) for p in ordered_cases)
    pattern = re.compile(catch_all)

    def replacer(match):
        replacement_pattern = replacements[match.lastindex]
        return match.expand(replacement_pattern)

    return partial(pattern.sub, replacer)

def absolute_backreference(text, n):
    ref_pat = re.compile(r"\\([0-99])")

    def replacer(match):
        return "\\{}".format(int(match.group(1)) + n)

    return ref_pat.sub(replacer, text)

def multireplace(text, repldict, prefix='', suffix=''):
    new_repldict = {k:prefix + v + suffix for (k,v) in repldict.items()}
    replacer = build_replacer(new_repldict) # must not be regex
    return replacer(text)

#pattern_to_replacement = {'&&': 'and', '!([a-zA-Z_]+)': r'not \1'}
#replacer = build_replacer(pattern_to_replacement)
#print(replacer("!this.exists()"))