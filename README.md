# ouman-eh-800-api

[![PyPI version](https://img.shields.io/pypi/v/ouman-eh-800-api.svg)](https://pypi.org/project/ouman-eh-800-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/ouman-eh-800-api.svg)](https://pypi.org/project/ouman-eh-800-api/)
[![License](https://img.shields.io/pypi/l/ouman-eh-800-api.svg)](https://github.com/Markus98/ouman-eh-800-api/blob/main/LICENSE)

Async Python client for communicating with the [Ouman EH-800 heating controller](https://ouman.fi/en/product/ouman-eh-800-and-eh-800b/).

## Installation

```bash
pip install ouman-eh-800-api
```

## Usage

```python
import asyncio
import aiohttp
from ouman_eh_800_api import (
    OumanEh800Client,
    L1BaseEndpoints,
    SystemEndpoints,
    HomeAwayControl,
    OperationMode,
)


async def main():
    async with aiohttp.ClientSession() as session:
        client = OumanEh800Client(
            session=session,
            address="http://192.168.1.100",
            username="user",
            password="password",
        )

        # Authenticate
        await client.login()

        # Detect the registries that match the device's current configuration
        # (curve type, room sensor, L2, relay mode) and read every endpoint
        # in one batch.
        registry_set = await client.get_active_registries()
        values = await client.get_values(registry_set)

        print(f"Outside temp: {values[SystemEndpoints.OUTSIDE_TEMPERATURE]} °C")
        print(f"L1 supply temp: {values[L1BaseEndpoints.SUPPLY_WATER_TEMPERATURE]} °C")

        # Set home/away mode
        await client.set_endpoint_value(
            SystemEndpoints.HOME_AWAY_MODE, HomeAwayControl.HOME
        )

        # Set L1 operation mode
        await client.set_endpoint_value(
            L1BaseEndpoints.OPERATION_MODE, OperationMode.AUTOMATIC
        )

        await client.logout()


asyncio.run(main())
```

## Features

- Async API using aiohttp
- Read sensor values (temperatures, valve positions, etc.)
- Control heating circuits (operation mode, temperature curves, etc.)
- Set home/away mode
- Support for L1 and L2 heating circuits
- Support for optional room sensors

## Available Registries

The library splits endpoints into small "fragment" registries. For a given
device configuration only a subset is active; `client.get_active_registries()`
returns the right composition automatically. Manual composition via
`OumanRegistrySet([...])` is also supported.

| Registry | Description |
|----------|-------------|
| `SystemEndpoints` | System-wide (outside temp, home/away, relay status, etc.) |
| `L1BaseEndpoints` / `L2BaseEndpoints` | Per-circuit endpoints always queryable when the circuit is in use |
| `L1ThreePointCurve` / `L1FivePointCurve` | L1 heating-curve setpoints (mutually exclusive) |
| `L2ThreePointCurve` / `L2FivePointCurve` | L2 heating-curve setpoints (mutually exclusive) |
| `L1NoRoomSensor` / `L1RoomSensor` | L1 endpoints whose IDs differ depending on whether a room sensor is installed |
| `L2NoRoomSensor` / `L2RoomSensor` | Same for L2 |
| `L1ConstantTempMode` | Setpoint exposed when L1 heating mode is constant-temperature controller |
| `RelayPumpSummerStop`, `RelayTemperature`, `RelayTempDifference`, `RelayL1ValvePosition`, `RelayTimeProgram` | Relay-control override; one active depending on the configured relay mode |

## Requirements

- Python 3.13+
- aiohttp

## Disclaimer

This client has been developed and tested with the Ouman EH-800 unit that was available to the developer. It did not have all features enabled, thus there may be missing features or bugs.

The L2 heating circuit and room sensor endpoints have not been verified.

## Contributing

Pull requests for new features or bug fixes are welcome. Please open an issue first to discuss major changes.

## License

[Apache-2.0](LICENSE)
