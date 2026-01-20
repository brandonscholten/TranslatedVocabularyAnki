import deepl
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

"""
This file contains functions related to translation
"""

@lru_cache
def get_language_names() -> dict:
    """Get dictionary mapping of language code to full language names"""
    #TODO: why two loops for this? Are these lists different? Should there be two dictionaries?
    # I guess the use of lru_cache makes this not so terrible
    #TODO: the plan is to change this to use LibreTranslate instead of Deepl
    # A secondary translator will need to be used for verification that isn't Google Translate
    deepl_translator = deepl.Translator(
        auth_key=Path(".deepl_auth").read_text().strip()
    )

    source_language_names = {}
    target_language_names = {}
    for language in deepl_translator.get_source_languages():
        source_language_names[language.code.lower()] = language.name

    for language in deepl_translator.get_target_languages():
        target_language_names[language.code.lower()] = language.name

    return {
        "source" : source_language_names,
        "target" : target_language_names
    }


def translate_deepl(
    input_vocab: dict[int, str],
    target_language: str,
    source_language: str,
    verification_language: str,
) -> dict[int, tuple[str, str]]:
    """Translates the input vocabulary to the target language and verification
    language using Deepl.
    Uses a Deepl API key that should be stored at `.deepl_auth`.
    """
    output_vocab = {}

    # Separate function to translate a single phrase so we can multithread
    def translate_phrase(args):
        id, phrase = args

        deepl_translator = deepl.Translator(
            auth_key=Path(".deepl_auth").read_text().strip()
        )

        deepl_result = deepl_translator.translate_text(
            phrase,
            source_lang=source_language,
            target_lang=target_language,
            split_sentences=0,
        )

        verification_result = deepl_translator.translate_text(
            deepl_result.text,
            source_lang=target_language,
            target_lang=verification_language,
            split_sentences=0,
        )

        output_vocab[id] = (deepl_result.text, verification_result.text)

    with ThreadPoolExecutor() as executor:
        for _ in tqdm(
            executor.map(translate_phrase, input_vocab.items()),
            desc="Obtaining Deepl translations...",
            total=len(input_vocab),
        ):
            # We only loop to get a nice progress bar
            pass

    return output_vocab


