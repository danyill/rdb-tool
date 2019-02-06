#!/usr/bin/env python3

def flatten(l):
    # flatten list of lists by 1
    return [item for sublist in l for item in sublist]

def unique(l):
    # unique items in a list
    return list(set(l))

def remove_empty(mylist):
    return [l for l in mylist if l]