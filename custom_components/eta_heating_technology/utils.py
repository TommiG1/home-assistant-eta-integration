"""Utils for eta_heating_technology."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .api import Value
from .const import ETA_BINARY_SENSOR_VALUES_DE, ETA_SENSOR_UNITS, ETA_STRING_SENSOR_VALUES_DE, EtaSensorType

if TYPE_CHECKING:
    from .api import Object


def determine_sensor_type(value: Value) -> EtaSensorType | None:
    """Determine the sensor type based on the value's unit and string representation."""
    sensor_unit = value.unit
    if sensor_unit in ETA_SENSOR_UNITS:
        return EtaSensorType.SENSOR
    if value.value in ETA_BINARY_SENSOR_VALUES_DE:
        return EtaSensorType.BINARY_SENSOR
    if value.value in ETA_STRING_SENSOR_VALUES_DE:
        return EtaSensorType.STRING_SENSOR
    # Fallback: any unrecognized value is treated as a string sensor
    # (covers output states, unknown codes, unitless numeric values, etc.)
    return EtaSensorType.STRING_SENSOR


def entity_data_key(obj: Object) -> str:
    """
    Return the coordinator / unique_id key for an ETA object.

    URIs are unique; full_name is not (ETA exposes inactive twin endpoints
    with the same menu path, e.g. Heizgrenze für Heizen).
    """
    return obj.uri


def entity_display_name(obj: Object, all_objects: list[Object]) -> str:
    """
    Return a human-readable entity name.

    When several objects share the same full_name, append the last URI segment
    so both remain distinguishable in the UI.
    """
    duplicate_count = sum(1 for other in all_objects if other.full_name == obj.full_name)
    if duplicate_count <= 1:
        return obj.full_name
    uri_id = obj.uri.rstrip("/").rsplit("/", maxsplit=1)[-1]
    return f"{obj.full_name} ({uri_id})"
