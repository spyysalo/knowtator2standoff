#!/bin/bash

./convertcraft.sh
cp craft-2.0/articles/txt/*.txt standoff/

perl -p -i -e 's/^(\S+\t)(?:PR|EntrezGene)/${1}GGP/' standoff/*.ann
perl -p -i -e 's/^(\S+\t)(?:NCBITaxon|taxonomic_rank)/${1}Taxon/' standoff/*.ann
for f in standoff/*.ann; do
    egrep -v '^T[0-9]+'$'\t''(subspecies|species|phylum|kingdom) ' $f > tmp
    mv tmp $f
done

for f in standoff/*.ann; do
    python scripts/remove-duplicates.py $f > tmp
    mv tmp $f
done

for f in standoff/*.ann; do
    python scripts/resolveoverlaps.py $f > tmp
    mv tmp $f
done

rm -rf split-standoff
mkdir -p split-standoff/{train,devel,test}
for s in train devel test; do
    cat split/$s.txt | while read i; do
	cp standoff/$i.{txt,ann} split-standoff/$s
    done
done

for s in train devel test; do
    python standoff2conll/standoff2conll.py -a split-standoff/$s > $s.tsv
done
