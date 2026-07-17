"""Speechmatics Melia language coverage (Batch SaaS).

Source: https://docs.speechmatics.com/speech-to-text/languages
Melia-1 transcribes these *individual* language codes and can code-switch
across them. It does **not** use bilingual pack codes (`en_ta`, etc.) and
does **not** support Speechmatics `translation_config` — English ops text is
produced in Verge via aimlapi after Melia ASR (see ``transcribe.py``).
"""

from __future__ import annotations

# Individual Melia-capable codes from Speechmatics language table (ISO).
# Packs like ar_en / en_ta are Standard/Enhanced-only — do not send to Melia.
MELIA_LANGUAGES: dict[str, str] = {
    "ar": "Arabic",
    "ba": "Bashkir",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bg": "Bulgarian",
    "yue": "Cantonese",
    "ca": "Catalan",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "gl": "Galician",
    "de": "German",
    "el": "Greek",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "id": "Indonesian",
    "ia": "Interlingua",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "ms": "Malay",
    "mt": "Maltese",
    "cmn": "Mandarin",
    "mr": "Marathi",
    "mn": "Mongolian",
    "no": "Norwegian",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovakian",
    "sl": "Slovenian",
    "es": "Spanish",
    "sw": "Swahili",
    "sv": "Swedish",
    "ta": "Tamil",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "ug": "Uyghur",
    "vi": "Vietnamese",
    "cy": "Welsh",
}

# Plant-radio priority for India / Gulf ops (all Melia-supported).
PLANT_RADIO_HINTS_DEFAULT = ("en", "hi", "ta", "ur", "bn", "mr")

# Requested in .env historically but NOT in Speechmatics Melia table today.
UNSUPPORTED_PLANT_REQUESTS: dict[str, str] = {
    "te": "Telugu — not in Speechmatics Melia language table (as of docs pull)",
    "kn": "Kannada — not in Speechmatics Melia language table (as of docs pull)",
}


def melia_language_catalog() -> list[dict[str, str]]:
    return [{"code": code, "name": name} for code, name in sorted(MELIA_LANGUAGES.items())]


def filter_hints(raw: list[str] | tuple[str, ...]) -> tuple[list[str], list[str]]:
    """Return (valid Melia hints, skipped unsupported codes)."""
    ok: list[str] = []
    skipped: list[str] = []
    for code in raw:
        c = code.strip().lower()
        if not c:
            continue
        if c in MELIA_LANGUAGES:
            if c not in ok:
                ok.append(c)
        else:
            skipped.append(c)
    return ok, skipped
