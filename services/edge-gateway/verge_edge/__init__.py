"""Edge Gateway — OPC-UA/MQTT ingest, normalization, store-and-forward (P7)."""

from .autonomy import EdgeAutonomy
from .buffer import StoreAndForward
from .normalize import NormalizationError, normalize_mqtt, normalize_opcua

__all__ = [
    "EdgeAutonomy",
    "NormalizationError",
    "StoreAndForward",
    "normalize_mqtt",
    "normalize_opcua",
]
__version__ = "0.3.0"
