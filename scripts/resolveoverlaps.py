#!/usr/bin/env python

# Eliminate textbound annotations overlapped by other annotations in
# brat-flavored standoff version of CRAFT data.

from __future__ import print_function

import os
import sys
import re
import codecs

from collections import defaultdict


DEFAULT_ENCODING='utf-8'


class Annotation(object):
    def __init__(self, ln, id_, data):
        self.ln = ln
        self.id = id_
        self.data = data

        self.removed = False
        self._spans = None

    def is_textbound(self):
        return self.id[0] == 'T'

    @property
    def type(self):
        return self.data.split('\t')[0].split(' ', 1)[0]

    @property
    def spans(self):
        if self._spans is None:
            if not self.is_textbound():
                raise NotImplementedError('only textbounds have spans')
            fields = self.data.split('\t')
            type_, rest = fields[0].split(' ', 1)
            spans = [s.split(' ') for s in rest.split(';')]
            spans = [(int(s[0]), int(s[1])) for s in spans]
            self._spans = spans
        return self._spans

    @property
    def start(self):
        return min(s[0] for s in self.spans)

    @property
    def end(self):
        return max(s[1] for s in self.spans)

    def overlaps(self, other):
        # Note: annotations treated as continuous for comparison
        t1start, t1end = self.start, self.end
        t2start, t2end = other.start, other.end
        if t1end <= t2start or t1start >= t2end:
            return False
        else:
            return True

    def __unicode__(self):
        return u'%s\t%s' % (self.id, self.data)


def pick_removed(t1, t2):
    # prefer to remove shorter, remove later if identical length
    t1len = t1.end - t1.start
    t2len = t2.end - t2.start
    if t1len < t2len:
        return t1, t2
    elif t2len < t1len:
        return t2, t1
    elif t1.start < t2.start:
        return t1, t2
    elif t2.start < t1.start:
        return t2, t1
    elif t1.ln < t2.ln:
        return t1, t2
    else:
        return t2, t1


# Pairs of annotation types where the former is preferred over the
# latter so that overlaps between annotations having the pair of types
# are resolved by removing the one with the latter type. Some typical
# cases resolved by these preferences:
#
# - SO vs. independent_continuant: mutant, wild-type, WT, transgenic
# - CL vs. GO: cell, cells, cellular
# - CHEBI vs. SO: mRNA, amino acid, nucleotide, cysteine, proline
# - GO vs. SO: chromosome, chromosomal, transmembrane
# - GGP vs. CHEBI: insulin, Gh, cytochrome c, myoglobin
# - GGP vs. GO: collagen, PCNA, CII, FAS
# - SO vs. GGP: rRNA, ribosomal RNA
# - GO vs. CHEBI: haemoglobin
_preferred_types = [
    ('SO', 'independent_continuant'),
    ('CL', 'GO'),
    ('CHEBI', 'SO'),
    ('GO', 'SO'),
    ('GGP', 'CHEBI'),
    ('GGP', 'GO'),
    ('SO', 'GGP'),
    ('GO', 'CHEBI'),
    ('SO', 'Taxon'),
]


def resolve_identical_spans(a1, a2):
    if a1.removed or a2.removed:
        return
    for keep, remove in _preferred_types:
        if a1.type == keep and a2.type == remove:
            a2.removed = True
        elif a2.type == keep and a1.type == remove:
            a1.removed = True
            a1, a2 = a2, a1
        if a2.removed:
            print(u'Remove {} due to overlap with {}'.format(a2, a1),
                  file=sys.stderr)
            return
    print(u'Unresolved: {} vs {}'.format(a2, a1), file=sys.stderr)


def resolve_overlapped(source, out=None, encoding=DEFAULT_ENCODING):
    if isinstance(source, basestring):
        with codecs.open(source, encoding=encoding) as f:
            return resolve_overlapped(f)

    if out is None:
        out = codecs.getwriter(encoding)(sys.stdout)

    annotations = []
    for ln, line in enumerate(source):
        line = line.rstrip('\n')
        id_, data = line.split('\t', 1)
        annotations.append(Annotation(ln, id_, data))

    textbounds = [a for a in annotations if a.is_textbound()]

    # Resolve annotations with identical spans by type
    anns_by_span = defaultdict(list)
    for a in textbounds:
        anns_by_span[tuple(a.spans)].append(a)
    for anns in anns_by_span.values():
        if len(anns) < 2:
            continue
        for a1 in anns:
            for a2 in anns:
                if a1 is a2 or a1.removed or a2.removed:
                    continue
                resolve_identical_spans(a1, a2)

    # Resolve other annotations by length
    # TODO: avoid O(N^2)
    for t1 in textbounds:
        if t1.removed:
            continue
        for t2 in textbounds:
            if t1 is t2 or t1.removed or t2.removed or not t1.overlaps(t2):
                continue
            t, o = pick_removed(t1, t2)
            try:
                print(u'Remove {} due to overlap with {}'.format(t, o),
                      file=sys.stderr)
            except UnicodeEncodeError:
                print(u'Remove %s due to overlap with %s'.format(t.id, o.id),
                      file=sys.stderr)
            t.removed = True

    removed_count = 0
    for a in annotations:
        if a.removed:
            removed_count += 1
        else:
            print(unicode(a), file=out)

    if removed_count != 0:
        print('removed {} overlapped annotations from {}'.format(
            removed_count, os.path.basename(source.name)), file=sys.stderr)


def main(argv):
    for fn in argv[1:]:
        resolve_overlapped(fn)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
