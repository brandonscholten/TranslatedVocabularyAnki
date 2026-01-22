import string
from pathlib import Path
from typing import Optional
import translate
import genanki

"""
This file contains functions for CRUD operations on anki decks
"""

def create_anki_deck(
    translated_vocab: dict[int, dict],
    *,
    target_language: str,
    source_language: str,
    verification_language: str,
    deck_id: int,
    output_file: Path,
    add_reverse_cards: bool = True,
    deck_name: Optional[str] = None
):
    language_name = translate.get_language_names()[target_language]
    source_language_name = translate.get_language_names()[source_language]
    verification_language_name = translate.get_language_names()[verification_language]

    model = genanki.Model(
        model_id=deck_id, # To make sure the model is unique for each deck
        name=f"{source_language_name}<->{language_name} Translated Vocab Flashcards", #TODO: make this configurable
        fields=[
            {"name": source_language_name},
            {"name": language_name},
            {"name": verification_language_name},
            {"name": "SoundFile"}
        ],
        templates = [
            # One card from source language to target langauge
            {
                "name": f"{source_language_name} -> {language_name}",
                "qfmt": string.Template(
                    "{{$source}}<br/>({{$verification}})"
                ).substitute(
                    source=source_language_name,
                    verification=verification_language_name,
                ),
                "afmt": string.Template(
                    '{{FrontSide}}<hr id="answer">{{$language_name}}<br/>{{SoundFile}}'
                ).substitute(language_name=language_name)
            }
        ],
        css=".card { font-family: arial; font-size: 24px; text-align: center; color: black; background-color: white;}",
    )

    # And another card from target language to source language
    if add_reverse_cards:
        model.templates.append(
            {
                "name": f"{language_name} -> {source_language_name}",
                "qfmt": string.Template(
                    "{{$language_name}}<br/>{{SoundFile}}"
                ).substitute(language_name=language_name),
                "afmt": string.Template(
                    '{{FrontSide}}<hr id="answer">{{$source}}<br/>({{$verification}})'
                ).substitute(
                    source=source_language_name,
                    verification=verification_language_name,
                ),
            }
        )

    deck = genanki.Deck(
        deck_id=deck_id,
        name=deck_name or f"Translated {language_name} vocabulary",
        description={
            f"Automatically translated {source_language_name} <-> {language_name} vocabulary."
        },
    )

    for id, entry in translated_vocab.items():
        note = genanki.Note(
            model=model,
            fields=[
                entry[source_language],
                entry[target_language],
                entry[verification_language],
                f'[sound:{Path(entry["pronunciation_file"])}]',
            ],
            tags=entry["tags"],
            guid=f"{deck_id}_{id}",
        )
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = [v["pronunciation_file"] for v in translated_vocab.values()]
    package.write_to_file(output_file)

    return deck_id
