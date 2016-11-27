#!/usr/bin/env python

# Eliminate textbound annotations overlapped by longer annotations in
# brat-flavored standoff annotation.

import os
import sys
import re
import codecs

DEFAULT_ENCODING='utf-8'

class Annotation(object):
    def __init__(self, ln, id_, data):
        self.ln = ln
        self.id = id_
        self.data = data

        self.removed = False
        self._span = None
        
    def is_textbound(self):
        return self.id[0] == 'T'

    def span(self):
        if self._span is None:
            if not self.is_textbound():
                raise NotImplementedError('only textbounds have spans')
            fields = self.data.split('\t')
            type_, rest = fields[0].split(' ', 1)
            spans = rest.split(';')
            if len(spans) > 1:
                raise NotImplementedError('discontinuous spans not supported')
            span = spans[0].split(' ')
            start, end = int(span[0]), int(span[1])
            self._span = (start, end)
        return self._span

    def overlaps(self, other):
        t1start, t1end = self.span()
        t2start, t2end = other.span()
        if t1end <= t2start or t1start >= t2end:
            return False
        else:
            return True
    
    def __unicode__(self):
        return u'%s\t%s' % (self.id, self.data)

def pick_removed(t1, t2):
    # prefer to remove shorter, remove later if identical length
    t1start, t1end = t1.span()
    t2start, t2end = t2.span()
    t1len = t1end - t1start
    t2len = t2end - t2start
    if t1len < t2len:
        return t1, t2
    elif t2len < t1len:
        return t2, t1
    elif t1start < t2start:
        return t1, t2
    elif t2start < t1start:
        return t2, t1
    elif t1.ln < t2.ln:
        return t1, t2
    else:
        return t2, t1
        
def remove_overlapped(source, out=None, encoding=DEFAULT_ENCODING):
    if isinstance(source, basestring):
        with codecs.open(source, encoding=encoding) as f:
            return remove_overlapped(f)

    if out is None:
        out = codecs.getwriter(encoding)(sys.stdout)

    annotations = []
    for ln, line in enumerate(source):
        line = line.rstrip('\n')
        id_, data = line.split('\t', 1)
        annotations.append(Annotation(ln, id_, data))

    textbounds = [a for a in annotations if a.is_textbound()]

    # TODO: avoid O(N^2)
    for t1 in textbounds:
        for t2 in textbounds:
            if t1 is t2 or t1.removed or t2.removed or not t1.overlaps(t2):
                continue
            t, o = pick_removed(t1, t2)
            try:
                print >> sys.stderr, u"Eliminate %s due to overlap with %s" \
                    % (t, o)
            except UnicodeEncodeError:
                print >> sys.stderr, u"Eliminate %s due to overlap with %s" \
                    % (t.id, o.id)
            t.removed = True

    removed_count = 0
    for a in annotations:
        if a.removed:
            removed_count += 1
        else:
            print >> out, unicode(a)

    if removed_count != 0:
        print >> sys.stderr, 'removed %d overlapped annotations from %s' % \
            (removed_count, os.path.basename(source.name))
            
def main(argv):
    for fn in argv[1:]:
        remove_overlapped(fn)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
