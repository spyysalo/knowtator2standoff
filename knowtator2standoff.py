#!/usr/bin/env python

from __future__ import print_function

import sys
import re
import io
import xml.etree.cElementTree as ET

from collections import defaultdict
from os import path
from logging import warn


DOCDIR = 'craft-2.0/articles/txt/'    # TODO: CLI argument

# Mapping from CRAFT to standoff types
type_map = {
    'Entrez Gene sequence': 'EntrezGene',
    'organism': 'NCBITaxon',
}


class FormatError(Exception):
    pass


class Annotation(object):
    """Knowtator annotation."""

    def __init__(self, spans, texts, mention_id):
        self.spans = spans
        self.texts = texts
        self.mention_id = mention_id
        self.mention = None

    @property
    def type(self):
        if self.mention is None:
            raise ValueError('no mention (call map_mentions?)')
        type_ = self.mention.type
        type_ = type_map.get(type_, type_)
        return type_

    def to_standoff(self):
        t_id = next_free_id('T')
        type_ = self.type.replace(' ', '_')
        spans = ';'.join('{} {}'.format(s, e) for s, e in self.spans)
        texts = u' '.join(self.texts)        
        t_ann = u'{}\t{} {}\t{}'.format(t_id, type_, spans, texts)
        return [t_ann]

    @classmethod
    def from_xml(cls, e, doc_text):
        """Return Annotation from ElementTree element."""
        spans = []
        for s in e.findall('span'):
            spans.append((int(s.get('start')), int(s.get('end'))))
        if not spans:
            raise FormatError('no spans for annotation')
        text = findonly(e, 'spannedText').text
        if not text:
            raise FormatError('no text for annotation')
        texts = text.split(' ... ')    # Resolve discontinuous annotations
        if len(spans) != len(texts):
            raise FormatError('{} spans, {} texts'.format(len(self.spans),
                                                          len(self.texts)))
        fixed_spans = []
        for span, text in zip(spans, texts):
            start, end = span
            if len(text) != end-start:
                msg = 'text length mismatch: "{}" ({}) vs {}-{} ({})'.format(
                    text.encode('utf-8'), len(text), start, end, end-start)
                if doc_text[start:start+len(text)] == text:
                    msg += ' (adjust end: "{}" to "{}")'.format(
                        doc_text[start:end].encode('utf-8'),
                        doc_text[start:start+len(text)].encode('utf-8'))
                    end = start+len(text)
                elif doc_text[end-len(text):end] == text:
                    msg += ' (adjust start: "{}" to "{}")'.format(
                        doc_text[start:end].encode('utf-8'),
                        doc_text[end-len(text):end].encode('utf-8'))
                    start = end-len(text) 
                else:
                    msg += ' (failed to adjust)'
                warn(msg)
            if len(text) != end-start:
                raise FormatError(
                    'Text mismatch: "{}" (len {}) vs "{}" ({}-{})'.format(
                        text.encode('utf-8'), len(text),
                        doc_text[start:end].encode('utf-8'), start, end))
            fixed_spans.append((start, end))
        spans = fixed_spans
        mention_id = findonly(e, 'mention').get('id')
        return cls(spans, texts, mention_id)


def findonly(e, tag):
    """Return only child of ElementTree element with given tag."""
    found = e.findall(tag)
    if len(found) != 1:
        raise FormatError('expected single {} child, found {}'.format(
            tag, len(found)))
    return found[0]


def next_free_id(prefix):
    idx = next_free_id.id_map[prefix] + 1
    next_free_id.id_map[prefix] += 1
    return prefix + str(idx)
next_free_id.id_map = defaultdict(int)


def reset_next_free_id():
    next_free_id.id_map = defaultdict(int)


class ClassMention(object):
    """Knowtator ClassMention."""

    def __init__(self, id_, class_id, text):
        self.id = id_
        self.class_id = class_id
        self.text = text

    @property
    def type(self):
        m = re.match(r'^([a-zA-Z]+):(\d+)$', self.class_id)
        if m:
            return m.group(1)    # TYPE:NUM ontology ID
        else:
            return self.class_id
        
    @classmethod
    def from_xml(cls, e):
        """Return ClassMention from ElementTree element."""
        id_ = e.get('id')
        c = findonly(e, 'mentionClass')
        class_id = c.get('id')
        text = c.text
        return cls(id_, class_id, text)




class StringSlotMention(object):
    """Knowtator StringSlotMention."""

    def __init__(self, id_, slot, value):
        self.id = id_
        self.slot = slot
        self.value = value

    @property
    def type(self):
        return self.slot

    @classmethod
    def from_xml(cls, e):
        """Return StringSlotMention from ElementTree element."""
        id_ = e.get('id')
        slot = findonly(e, 'mentionSlot').get('id')
        value = findonly(e, 'stringSlotMentionValue').get('value')
        return cls(id_, slot, value)


class IntegerSlotMention(object):
    """Knowtator IntegerSlotMention."""

    def __init__(self, id_, slot, value):
        self.id = id_
        self.slot = slot
        self.value = value

    @property
    def type(self):
        return self.slot

    @classmethod
    def from_xml(cls, e):
        """Return IntegerSlotMention from ElementTree element."""
        id_ = e.get('id')
        slot = findonly(e, 'mentionSlot').get('id')
        value = findonly(e, 'integerSlotMentionValue').get('value')
        return cls(id_, slot, value)


class BooleanSlotMention(object):
    """Knowtator BooleanSlotMention."""

    def __init__(self, id_, slot, value):
        self.id = id_
        self.slot = slot
        self.value = value

    @property
    def type(self):
        return self.slot

    @classmethod
    def from_xml(cls, e):
        """Return BooleanSlotMention from ElementTree element."""
        id_ = e.get('id')
        slot = findonly(e, 'mentionSlot').get('id')
        value = findonly(e, 'booleanSlotMentionValue').get('value')
        return cls(id_, slot, value)


class ComplexSlotMention(object):
    """Knowtator ComplexSlotMention."""

    def __init__(self, id_, slot, values):
        self.id = id_
        self.slot = slot
        self.values = values

    @property
    def type(self):
        return self.slot

    @classmethod
    def from_xml(cls, e):
        """Return ComplexSlotMention from ElementTree element."""
        id_ = e.get('id')
        slot = findonly(e, 'mentionSlot').get('id')
        values = [c.get('value') for c in e.findall('complexSlotMentionValue')]
        return cls(id_, slot, values)


def get_text(docid, docdir=DOCDIR, encoding='utf-8'):
    if docid not in get_text.text_by_docid:
        fn = path.join(docdir, docid)
        with io.open(fn, encoding=encoding) as f:
            text = f.read()
        get_text.text_by_docid[docid] = text
    return get_text.text_by_docid[docid]
get_text.text_by_docid = {}


_mention_class_map = {
    'classMention': ClassMention,
    'complexSlotMention': ComplexSlotMention,
    'integerSlotMention': IntegerSlotMention,
    'booleanSlotMention': BooleanSlotMention,
    'stringSlotMention': StringSlotMention,
}


def load_knowtator_xml(fn):
    tree = ET.parse(fn)
    root = tree.getroot()
    docid = root.get('textSource')
    text = get_text(docid)
    annotations = []
    mentions = []
    for e in root:
        try:
            if e.tag == 'annotation':
                annotations.append(Annotation.from_xml(e, text))
            elif e.tag in _mention_class_map:
                mentions.append(_mention_class_map[e.tag].from_xml(e))
            else:
                raise FormatError('unexpected element {}'.format(e.tag))
        except FormatError, error:
            print('error parsing {}: {} ({})'.format(fn, error, e),
                  file=sys.stderr)
    return docid, annotations, mentions


def map_mentions(annotations, mentions):
    mention_by_id = {}
    for m in mentions:
        assert m.id not in mention_by_id, 'duplidate id: {}'.format(m.id)
        mention_by_id[m.id] = m
    for a in annotations:
        a.mention = mention_by_id[a.mention_id]


def main(argv):
    if len(argv) < 2:
        print('Usage: {} [FILE [...]]'.format(__file__))
        return 1

    annotations_by_id = defaultdict(list)
    for fn in argv[1:]:
        try:
            docid, annotations, mentions = load_knowtator_xml(fn)
            map_mentions(annotations, mentions)
            annotations_by_id[docid].extend(annotations)
        except Exception, e:
            print('failed to parse {}: {}'.format(fn, e), file=sys.stderr)
    for docin, annotations in annotations_by_id.items():
        reset_next_free_id()
        for a in annotations:
            for t in a.to_standoff():
                print(t.encode('utf-8'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
