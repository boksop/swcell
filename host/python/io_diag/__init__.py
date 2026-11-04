"""Independent SwCell board-peripheral diagnostics; no CPU dependencies."""
from .capture import parse_record, StateCollector
__all__ = ['parse_record', 'StateCollector']
