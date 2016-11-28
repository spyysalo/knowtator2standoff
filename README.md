# knowtator2standoff

Knowtator to standoff format conversion for CRAFT corpus

## Quickstart

* Download CRAFT v2.0 data from http://bionlp-corpora.sourceforge.net/CRAFT/
* Unpack: `tar xzf craft-2.0.tar.gz`
* Convert annotations: `./convertcraft.sh`
* Copy in texts: `cp craft-2.0/articles/txt/*.txt standoff/`

## Modifications

* Merge gene/protein types: `perl -p -i -e 's/^(\S+\t)(?:PR|EntrezGene)/${1}GGP/' standoff/*.ann`
* Marge taxonomic types: `perl -p -i -e 's/^(\S+\t)(?:NCBITaxon|taxonomic_rank)/${1}Taxon/' standoff/*.ann`
* Remove rare non-physical types: `for f in standoff/*.ann; do egrep -v '^T[0-9]+'$'\t''(subspecies|species|phylum|kingdom) ' $f > tmp; mv tmp $f; done`
* Deduplicate: `for f in standoff/*.ann; do python scripts/remove-duplicates.py $f > tmp; mv tmp $f; done`
* Resolve overlaps: `for f in standoff/*.ann; do python scripts/resolveoverlaps.py $f > tmp; mv tmp $f; done`

## Train/devel/test split

    mkdir -p split-standoff/{train,devel,test}
    for s in train devel test; do cat split/$s.txt | while read i; do cp standoff/$i.{txt,ann} split-standoff/$s; done; done

## CoNLL conversion

    git clone git@github.com:spyysalo/standoff2conll.git
    for s in train devel test; do python standoff2conll/standoff2conll.py -a split-standoff/$s > $s.tsv; done
