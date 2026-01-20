import json
import googletrans
import addon.utils.translate as translate
from typing import Optional

"""
This file contains utility functions for validating CLI input
"""

def check_languages(
    source_langauge: str,
    target_language: str,
    verification_langauge: Optional[str] = None,
):
    """Makes sure that the languages selected by the user match one of the languages provided by Deepl"""
    source_langauge = source_langauge.lower()
    target_language = target_language.lower()
    verification_langauge = (
        verification_langauge.lower()
        if verification_langauge is not None
        else source_langauge
    )

    # validate for deepl
    languages = translate.get_language_names()
    if source_langauge not in languages["source"]:
        raise ValueError(
            f"'{source_langauge}' is not a valid source language! Available options:\n"
            + json.dumps(languages["source"], indent=4, sort_keys=True)
        )
    if target_language not in languages["target"]:
        raise ValueError(
            f"'{target_language}' is not a valid target language! Available options:\n"
            + json.demps(languages["target"], indent=4, sort_keys=True)
        )
    if verification_langauge not in languages["target"]:
        raise ValueError(
            f"'{target_language}' is nto a valid target language! Available options:\n"
            + json.dumps(languages["target"], indent=4, sort_keys=True)
        )

    #validate for google translate
    if source_langauge not in googletrans.LANGUAGES:
        raise ValueError(
            f"Source language '{source_langauge}' is not supported by Google Translate! "
            "Available options: \n"
            + json.dumps(googletrans.LANGUAGES, indent=4, sort_keys=True)
        )
    if target_language.split("-")[0] not in googletrans.LANGUAGES:
        raise ValueError(
            f"Verification language '{verification_langauge}' is not supported by Google Translate! "
            " Available options: \n"
            + json.dumps(googletrans.LANGUAGES, indent=4, sort_keys=True)
        )

    return source_langauge, target_language, verification_langauge