#!/bin/bash

# Convert subset of CRAFT corpus Knowtator annotations to standoff.

INDIR="craft-2.0/knowtator-xml"
OUTDIR="standoff"

# Omitted CRAFT annotations: go_bpmf, coreference, sections-and-typography
SUBSETS="chebi ncbitaxon cl entrezgene go_cc pr so"

files=$(for s in $SUBSETS; do ls "$INDIR/$s"; done | egrep '\.xml' | sort | uniq)
count=$(echo "$files" | wc -l)

echo "Converting" $count "files from $INDIR to $OUTDIR" >&2

rm -rf "$OUTDIR"
mkdir "$OUTDIR"

for f in $files; do
    # Collect files annotating the same document from subsets
    s=$(for s in $SUBSETS; do echo "$INDIR/$s/$f"; done)
    o="${f%.txt.knowtator.xml}"
    python knowtator2standoff.py $s > "$OUTDIR/$o.ann"
done
