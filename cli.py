import datetime
import json
import shutil
from pathlib import Path
from typing import Optional
import typer
import addon.utils.translate as translate
import addon.utils.csv as csv
import validation
import addon.utils.anki as anki

app = typer.Typer()

"""
This file contains the command-line interface for translating vocab lists.
"""

@app.command()
def translate_and_generate(
    vocab_path: Path = typer.Option(
        ..., help="Path to a vocabulary CSV file, e.g. Examples/vocab.csv"
    ),
    target_language: str = typer.Option(
        ..., help="The language to translate the vocabulary to."
    ),
    verification_language: str = typer.Option(
        None,
        help="The language used to backtranslate the translations to, so you can see whether the "
        "translations make any sense. Defaults to the source language.",
    ),
    source_language: str = typer.Option(
        "en", help="The language of the provided vocabulary file."
    ),
    deck_id: int = typer.Option(
        ...,
        help="Unique identifier for this Anki deck, e.g. 123456. Whenever you want to update a deck"
        " in Anki rather than create a new one, you should use the same identifier as you did last"
        " time. If you forgot the ID you used last time, check `info.json` in the generated zip "
        "file!",
    ),
    deck_name: Optional[str] = typer.Option(
        None, help="Name of the created deck as will be shown in Anki."
    ),
    add_reverse_cards: bool = typer.Option(
        True,
        help="Whether to add a duplicate of each card, but in the other direction. For example, if"
        "my source language is English and my target is Greek, this option will not only add "
        "English->Greek cards, but also Greek->English. Enabled by default.",
    ),
    output_dir: Path = typer.Option(Path("Output")),
):
    """Translates the vocabulary provided at `--vocab-path` to the target language, obtains TTS
    pronunciations and generates an Anki deck."""

    source_language, target_language, verification_language = validation.check_languages(
        source_language, target_language, verification_language
    )
    output_name = (
        f"{source_language}_{target_language}"
        + f"_{datetime.datetime.now().strftime('%y_%m_%d_%H_%M_%S')}"
    )
    temp_dir = output_dir.joinpath(output_name)
    temp_dir.mkdir(exist_ok=True, parents=True)

    input_vocab, tags = csv.load_vocab(vocab_path)

    # Do the translation work
    google_output = translate.translate_google(
        input_vocab, target_language=target_language, source_language=source_language
    )
    deepl_output = translate.translate_deepl(
        input_vocab,
        target_language=target_language,
        source_language=source_language,
        verification_language=verification_language,
    )

    # Postprocess results TODO: consider moving postprocessing into the translation module
    results = {}
    assert len(deepl_output) == len(google_output)
    for id, (deepl_translation, deepl_verification) in deepl_output.items():
        translation, verification = translate.process_translations(
            deepl_translation, google_output[id], deepl_verification
        )

        results[id] = {
            source_language: input_vocab[id],
            target_language: translation,
            verification_language: verification,
            "tags": tags[id],
        }

    # Save JSON output before moving on to pronunciations, since the translations are the bottleneck.
    # If something goes wrong, at least the translations will be saved.
    temp_dir.joinpath("data.json").write_text(json.dumps(results, indent="\t"))

    # Obtain pronunciation sound files and add them to results dict.
    results = translate.get_pronunciations(results, language=target_language, output_dir=temp_dir)

    # Update JSON with the newly added pronunciation files before moving on to Anki deck creation.
    # The JSON is easier to inspect and could be useful for non-Anki users as well.
    temp_dir.joinpath("data.json").write_text(json.dumps(results, indent="\t"))

    # Finally, create the actual Anki deck and save it to the output folder.
    deck_id = anki.create_anki_deck(
        results,
        target_language=target_language,
        source_language=source_language,
        verification_language=verification_language,
        add_reverse_cards=add_reverse_cards,
        output_file=output_dir.joinpath(f"{output_name}.apkg"),
        deck_id=deck_id,
        deck_name=deck_name,
    )

    # To clean things up, zip the JSON and all the sound files together, and delete the temporary
    # directory.
    shutil.copy(vocab_path, temp_dir.joinpath("vocab.csv"))
    temp_dir.joinpath("info.json").write_text(
        json.dumps(
            {
                "deck_id": deck_id,
                "source_language": source_language,
                "target_language": target_language,
                "verification_language": verification_language,
            }
        )
    )
    shutil.make_archive(
        str(output_dir.joinpath(output_name)),
        format="zip",
        root_dir=temp_dir,
    )
    shutil.rmtree(temp_dir)
    print(f"Done! Anki deck saved to {str(output_dir)}.")


if __name__ == "__main__":
    app()
