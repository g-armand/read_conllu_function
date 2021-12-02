"""
 DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                   Version 2, December 2004
 
Everyone is permitted to copy and distribute verbatim or modified
copies of this license document, and changing it is allowed as long
as the name is changed.
 
           DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
  TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

 0. You just DO WHAT THE FUCK YOU WANT TO.
"""

import sys
import json

from collections import Counter
from itertools import cycle, product
from warnings import warn


def is_projective(heads, is_padded=True):
    """Check whether a dependency tree is projective or not.

    This methods implements the test described in [1].

    [1] Gomez-Ródríguez and Nivre, A Transition-Based Parser for
    2-Planar Dependency Structures, ACL'10

    Parameters:
    -----------
    - heads, a list of ints
             the heads of each words **including padding symbols**
    """
    # remove START symbol
    edges = [(j, i) for i, j in enumerate(heads)]
    if is_padded:
        edges = edges[1:]

    for (i, k), (j, l) in product(edges, repeat=2):

        # XXX when does it happen?
        if i is None or j is None:
            continue

        # non-projectivity condition for partial trees
        if (j == k and (j > i > l or j < i < l)) or (i == l and (i > j > k or i < j < k)):
            return False

        # canonical non-projectivity condition
        if min(i, k) < min(j, l) < max(i, k) < max(j, l):
            return False

    return True


def pos_from_conllu(filehandler, max_sent=None, without_padding=True, keep_ud_tokenization=True, pos_mapper=None):

    if pos_mapper is None:
        pos_mapper = {}

    data = ((tuple(words), tuple(pos_mapper.get(pos, pos) for pos in features["cpos"]))
            for _, words, features, _, _ in read_conllu(filehandler, max_sent, without_padding, keep_ud_tokenization))
        
    yield from data


def read_conllu(filehandler, max_sent=None, without_padding=False, keep_ud_tokenization=True):
    """
    Read a file in CoNLLu format.

    Parameters
    ----------
    - `max_sent`, an integer
       if not `None`, only read the first `max_sent` of the file
    - `keep_ud_tokenization`, a boolean
       if `False`, compound words are not split (e.g. according to UD
       guideline the French word "aux" must be split into "à les") and
       only the original word is kept. The PoS of the original word is
       defined to be the concatenation of the PoS of the two splited words.
    """
    if isinstance(filehandler, str):
        filehandler = open(filehandler)

    header = "ID FORM LEMMA CPOS FPOS MORPHO HEAD LABEL X X".split()

    def parse_morpho(txt):
        if txt == "_":
            return {}

        return dict(t.split("=") for t in txt.split("|"))

    for n_sentence, (ex, metadata) in enumerate(read_tabular_file(filehandler,
                                                                  header,
                                                                  max_sent,
                                                                  keep_metadata=True,
                                                                  keep_ud_tokenization=keep_ud_tokenization)):
        words = [e["FORM"] for e in ex]
        if any(" " in w for w in words):
            # XXX should we do something?
            warn("space in word form")
        
        labels = [None] + [e["LABEL"] for e in ex] + [None]

        try:
            heads = list(int(e["HEAD"]) for e in ex)
        except ValueError:
            print(f"error parsing sentence {' '.join(e['FORM'] for e in ex)}")
            print("ignoring this sentence.")
            continue

        heads = [None] + [h if h != 0 else len(ex) + 1 for h in heads] + [None]

        cpos = [e["CPOS"] for e in ex]
        fpos = [e["FPOS"] for e in ex]
        lemma = [e["LEMMA"] for e in ex]
        morpho = [parse_morpho(e["MORPHO"]) if "MORPHO" in e else "_" for e in ex]

        if without_padding:
            features = {"cpos": cpos,
                        "fpos": fpos,
                        "morpho": morpho,
                        "lemma": lemma}

            yield metadata, words, features, [d - 1 for d in heads[1:-1]], labels[1:-1]
        else:
            features = {"cpos": pad_tokens(cpos),
                        "fpos": pad_tokens(fpos),
                        "morpho": pad_tokens(morpho),
                        "lemma": pad_tokens(lemma)}

            yield metadata, pad_tokens(words), features, heads, labels


def read_tabular_file(filehandler, header, max_sent, keep_metadata=False, keep_ud_tokenization=True):
    """
    Read `max_sent` sentences from a tabular file.

    Generates, for each example:
    - the position of the token in the sentence
    - the tokenized sentence
    - the features associated to each token
    - the gold heads
    - the labels of the dependency tree
    """
    cur_obser = []
    count_sent = 0
    sent_id = None
    metadata = {}
    for line_number, line in enumerate(filehandler):

        if line.startswith("#") and " = " in line:
            line = line.strip().split(" = ")
            key = line[0][1:].strip()
            value = " = ".join(line[1:])
            metadata[key] = value
            continue
        elif line.startswith("#"):
            continue

        line = line.strip().split("\t")

        if line == [""]:
            yield cur_obser, metadata if keep_metadata else cur_obser
            cur_obser = []
            count_sent += 1

            if max_sent is not None and count_sent >= max_sent:
                return

            continue

        assert len(line) == len(header), f"read {len(line)} tokens while I was expecting {len(header)} (token) in line n°{line_number + 1} '{line}'"

        # New version of the CoNLLU format uses empty nodes for the
        # analysis of ellipsis (enhanced dependency representation). I
        # still need to figure out how to represent/deal with
        # them. For the moment I am completly ignoring them
        if "." in line[0]:
            warn("corpus contains empty nodes. Ignore them")
            continue

        # In CoNLLU format, the original form of the different
        # words is kept as well as the tokenized form. For instance,
        # "c'était" is described by three lines: the first one
        # correspond to the original form ("c'était" with index "X-Y")
        # and the two others to the tokenized form ("c'" and "était"
        # with, resp., indexes "X" and "Y"). As all annotations refers
        # to the tokenized form, we keep it and discard the original
        # form.
        #
        # Note that, in UD tokenization, some contractions are
        # also split. For instance, in French, "du" is tokenized in
        # "de le" and, in German, "im" is tokenized in "in dem"
        if keep_ud_tokenization:
            if "-" not in line[0]:
                line = dict(zip(header, line))
                cur_obser.append(line)
            else:
                read_tabular_file.found_hyphen = True
        else:
            if "-" in line[0]:
                assert line[0].count("-") == 1

                line1 = dict(zip(header, next(filehandler).split()))
                line2 = dict(zip(header, next(filehandler).split()))

                d = dict(zip(header, line))
                line1["FORM"] = d["FORM"]
                line1["CPOS"] = line1["CPOS"] + "+" + line2["CPOS"]

                cur_obser.append(line1)
            else:
                cur_obser.append(dict(zip(header, line)))

    if cur_obser:
        yield cur_obser, metadata if keep_metadata else cur_obser


def pad_tokens(tokens):
    tokens.insert(0, '<start>')
    tokens.append('ROOT')
    return tokens


def write_feat(feat):
    if not feat:
        return "_"
    else:
        warn("ignoring morpho when serializing...")
        return "_"


def write_conllu(output, corpus, no_padding=False):

    # XXX can we write a CONLLU from partial information (e.g. when heads are not known)x
    for metadata, words, feat, heads, labels in corpus:
        metadata = "\n".join(f"# {key} = {value}" for key, value in sorted(metadata.items()))

        # XXX padding has not been tested
        if not no_padding:
            words = words[1:-1]

        output.write(metadata)
        output.write("\n")
        for i, word in enumerate(words, start=1):
            output.write(f"{i}\t{word}\t{feat['lemma'][i]}\t")
            output.write(f"{feat['cpos'][i]}\t{feat['fpos'][i]}\t")
            output.write(f"{write_feat(feat['morpho'][i])}\t")
            # XXX we are not taking care of padding
            output.write(f"{heads[i] if heads[i] <= len(heads) - 2 else 0}\t")
            output.write(f"{labels[i]}\t_\t_")
            output.write("\n")
        output.write("\n")
