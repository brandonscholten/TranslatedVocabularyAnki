from pathlib import Path

"""
This file contains functions for loading and exporting vocab to/from csv
"""

#TODO: the vocab should probably get it's own fancy data structure

def load_vocab(filepath: Path) -> tuple[dict[int, str], dict[int, list[str]]]:
    """Loads the vocabulary entries and tags from the provided CSV filepath"""
    input_vocab = filepath.read_text().strip().splitlines()

    vocab_dict, tag_dict = {}, {}
    for line in input_vocab:
        # Allow for comments
        if line.startswith("#"):
            continue
        index, phrase, *tags = line.strip().split("\t")
        index = int(index)
        if index in vocab_dict:
            raise ValueError(
                f"ID {index} of '{line}' is used twice! "
                f"First occurrence:\n'{index}\t{vocab_dict[index]}'"
            )

        vocab_dict[index] = phrase
        tag_dict[index] = tags

    return vocab_dict, tag_dict

def export_vocab(filepath: Path, vocab: tuple[dict[int, str], dict[int, list[str]]]):
    #TODO: write this, first figure out how to populate information from an existing anki deck
    #      might also ponder supporting small phrases
    return
