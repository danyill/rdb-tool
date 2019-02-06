#!/usr/bin/env python3

# https://stack, overflow.com/questions/2154249/identify-groups-of-continuous-numbers-in-a-list
def as_range(iterable): # not sure how to do this part elegantly
    l = list(iterable)
    if len(l) > 1:
        return '{0}-{1}'.format(l[0], l[-1])
    else:
        return '{0}'.format(l[0])

    return ','.join(as_range(g) for _, g in groupby(numberlist, key=lambda n, c=count(): n-next(c)))

def get_interval_range(data):
    from itertools import groupby
    from operator import itemgetter

    ranges =[]
    for key, group in groupby(enumerate(data), lambda i: i[0] - i[1]):
        group = list(map(itemgetter(1), group))
        group = list(map(int,group))
        ranges.append((group[0],group[-1]))
    return ranges

def provide_string_range(rng):
    output = []
    for lims in rng:
        #print(lims)
        if lims[0] == lims[1]:
            output.append(str(lims[0]))
        else:
            output.append(str(lims[0])+'-'+str(lims[1]))
    return ", ".join(output)