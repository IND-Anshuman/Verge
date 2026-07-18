"""Voice transcription and handover evidence helpers."""

from .alert_preview import alert_preview
from .languages import (
    MELIA_LANGUAGES,
    PLANT_RADIO_HINTS_DEFAULT,
    UNSUPPORTED_PLANT_REQUESTS,
    melia_language_catalog,
)
from .near_miss import near_miss_from_audio, near_miss_from_transcript
from .transcribe import (
    SpeechmaticsSettings,
    VoiceResult,
    speechmatics_status,
    transcribe_audio,
)

__all__ = [
    "MELIA_LANGUAGES",
    "PLANT_RADIO_HINTS_DEFAULT",
    "UNSUPPORTED_PLANT_REQUESTS",
    "SpeechmaticsSettings",
    "VoiceResult",
    "alert_preview",
    "melia_language_catalog",
    "near_miss_from_audio",
    "near_miss_from_transcript",
    "speechmatics_status",
    "transcribe_audio",
]

__version__ = "0.3.0"
