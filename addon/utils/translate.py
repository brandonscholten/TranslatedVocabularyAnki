import deepl
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from gtts import gTTS
import math

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

def translate_google(
        input_vocab: dict[int, str],
        target_language: str,
        source_language: str,
) -> dict[int, str]:
    """
    Batch-translates the entire input vocabulary to the target language using Google Translate.
    """

    google_translator = googletrans.Translator()
    values = list(input_vocab.values())
    batch_size = 20 #TODO make this configurable?
    translations = []

    # Google Translate doesn't distinguish between e.g. EN-US and EN-GB
    target_language = target_language.split("-")[0].lower()
    source_language = source_language.split("-")[0].lower()

    # Translate in batches and add outputs to translations list
    for start_idx in tqdm(
        range(0, len(values), batch_size),
        desc="Obtaining batch Google translations...",
        total=math.ceil(len(values) / batch_size),
    ):
        batch_translations = google_translator.translate(
            values[start_idx : start_idx + batch_size],
            source=source_language,
            dest=target_language,
        )
        translations.extend(batch_translations)
        start_idx += batch_size

    return {
        id: translation.text
        for id, translation in zip(input_vocab.keys(), translations, strict=True)
    }

def process_translations(deepl: str, google: str, verification: str) -> tuple[str, str]:
    """
    Postprocess the translation results for a given phrase to remove duplicates.
    """
    unique_phrases:set[str] = set()
    for part in deepl.split("/"): unique_phrases.add(part.lower())
    for part in google.split("/"): unique_phrases.add(part.lower())

    verification_phrases: set[str] = set()
    for part in verification.split("/"): verification_phrases.add(part.lower())

    return " / ".join(unique_phrases), " / ".join(verification_phrases)

def get_pronunciations(
    vocab: dict[int, str], language: str, output_dir: Path
) -> dict[int, dict]:
    """
    Use gTTS to obtain TTS samples for the entire vocabulary. Downloads MP3 files to the specified folder and
    returns the vocab with references to those files.
    """

    lang = language.lower()

    vocab_with_pronunciations = vocab.copy()
    for id, value in tqdm(
        vocab.items(), desc="Obtaining pronunciations...", total=len(vocab)
    ):
        speak = gTTS(text=value[language], lang=lang, slow=False) #TODO: make slowness configurable?
        path = str(output_dir.joinpath(f"{id}.mp3"))
        speak.save(path)
        vocab_with_pronunciations[id]["pronunciation_file"] = path

    return vocab_with_pronunciations
