#!/usr/bin/env python

# Print overlapping textbound annotations in brat-flavored standoff
# annotation.

from __future__ import print_function

import os
import sys
import re
import codecs

from collections import namedtuple


DEFAULT_ENCODING='utf-8'


Span = namedtuple('span', 'id type start end text')


def print_overlaps(source, out=None, encoding=DEFAULT_ENCODING):
    if isinstance(source, basestring):
        with codecs.open(source, encoding=encoding) as f:
            return print_overlaps(f)

    if out is None:
        out = codecs.getwriter(encoding)(sys.stdout)

    annotations = []
    for line in source:
        line = line.rstrip('\n')

        if not line:
            continue

        id_, data = line.split('\t', 1)
        if not id_.startswith('T'):
            continue

        type_span, text = data.split('\t')
        type_, spans = type_span.split(' ', 1)
        spans = [s.split(' ') for s in spans.split(';')]
        spans = [(int(s[0]), int(s[1])) for s in spans]
        start = min(s[0] for s in spans)
        end = max(s[1] for s in spans)

        annotations.append(Span(id_, type_, start, end, text))

    def ann_str(a):
        return u'{} {} {} ({})'.format(a.type, a.start, a.end, a.text)
        
    for a1 in annotations:
        for a2 in annotations:
            if a2.id <= a1.id:
                continue
            if a1.end <= a2.start or a1.start >= a2.end:
                continue
            print(u'{}\t{}\t{}'.format(source.name, ann_str(a1), ann_str(a2)),
                  file=out)
    
    # if duplicate_count != 0:
    #     print >> sys.stderr, 'removed %d duplicates from %s' % \
    #         (duplicate_count, os.path.basename(source.name))
            

def main(argv):
    for fn in argv[1:]:
        print_overlaps(fn)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
