"""Voice transcription and handover evidence helpers."""

from .alert_preview import alert_preview
from .near_miss import near_miss_from_audio, near_miss_from_transcript
from .transcribe import SpeechmaticsSettings, VoiceResult, transcribe_audio

__all__ = [
    "SpeechmaticsSettings",
    "VoiceResult",
    "alert_preview",
    "near_miss_from_audio",
    "near_miss_from_transcript",
    "transcribe_audio",
]

__version__ = "0.3.0"
