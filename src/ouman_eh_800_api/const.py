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


class RelayControl(StrEnum):
    """Manual override for the relay in temperature, temperature-difference,
    L1 valve-position, and time-program modes."""

    AUTO = "0"
    ON = "1"
    OFF = "2"


class PumpSummerStopControl(StrEnum):
    """Manual override for the relay in pump-summer-stop mode.

    Note that the value-1 / value-2 semantics are inverted compared to
    `RelayControl`: here `STOP` (force pump off) is `"1"` and `RUN` (force
    pump on) is `"2"`.
    """

    AUTO = "0"
    STOP = "1"
    RUN = "2"


ControlEnum = HomeAwayControl | OperationMode | RelayControl | PumpSummerStopControl
"""Type alias which contains all of the possible enums used for control operations"""

OumanValues = str | float | ControlEnum
"""Type alias for possible endpoint values: string, float, or a control enum."""


class OumanUnit(StrEnum):
    """Unit of measurement for endpoint values."""

    CELSIUS = "°C"
    SECOND = "s"
    PERCENT = "%"
