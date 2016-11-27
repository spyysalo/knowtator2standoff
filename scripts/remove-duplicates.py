#!/usr/bin/env python

# Eliminate duplicate textbound annotations from brat-flavored
# standoff annotation.

import os
import sys
import re
import codecs


DEFAULT_ENCODING='utf-8'


def remove_duplicates(source, out=None, encoding=DEFAULT_ENCODING):
    if isinstance(source, basestring):
        with codecs.open(source, encoding=encoding) as f:
            return remove_duplicates(f)

    if out is None:
        out = codecs.getwriter(encoding)(sys.stdout)

    seen, duplicate_count = set(), 0
    for line in source:
        line = line.rstrip('\n')

        if not line:
            print >> out
            continue

        id_, data = line.split('\t', 1)

        # Note: duplicates are detected as differing only in their
        # identifiers. No normalization is performed, so even a
        # difference in space will cause equivalents to be missed.
        if data in seen:
            duplicate_count += 1
        else:
            print >> out, '\t'.join((id_, data))
            seen.add(data)

    if duplicate_count != 0:
        print >> sys.stderr, 'removed %d duplicates from %s' % \
            (duplicate_count, os.path.basename(source.name))
            

def main(argv):
    for fn in argv[1:]:
        remove_duplicates(fn)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
