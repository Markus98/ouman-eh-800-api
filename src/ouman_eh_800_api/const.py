from enum import StrEnum


class HomeAwayControl(StrEnum):
    """Control enum for home/away mode setting."""

    HOME = "0"
    AWAY = "1"
    OFF = "2"


class OperationMode(StrEnum):
    """Control enum for heating circuit operation mode."""

    AUTOMATIC = "0"
    TEMPERATURE_DROP = "1"
    BIG_TEMPERATURE_DROP = "2"
    NORMAL_TEMPERATURE = "3"
    SHUTDOWN = "5"
    MANUAL_VALVE_CONTROL = "6"


ControlEnum = HomeAwayControl | OperationMode
"""Type alias which contains all of the possible enums used for control operations"""

OumanValues = str | float | ControlEnum
"""Type alias for possible endpoint values: string, float, or a control enum."""


class OumanUnit(StrEnum):
    """Unit of measurement for endpoint values."""

    CELSIUS = "°C"
    SECOND = "s"
    PERCENT = "%"
