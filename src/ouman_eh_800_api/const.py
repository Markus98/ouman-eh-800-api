from enum import StrEnum


class HomeAwayControl(StrEnum):
    HOME = "0"
    AWAY = "1"
    OFF = "2"


class OperationMode(StrEnum):
    AUTOMATIC = "0"
    TEMPERATURE_DROP = "1"
    BIG_TEMPERATURE_DROP = "2"
    NORMAL_TEMPERATURE = "3"
    SHUTDOWN = "5"
    MANUAL_VALVE_CONTROL = "6"


ControlEnum = HomeAwayControl | OperationMode


class OumanUnit(StrEnum):
    CELSIUS = "°C"
    SECOND = "s"
    PERCENT = "%"
