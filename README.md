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
    OumanRegistrySet,
    SystemEndpoints,
    L1Endpoints,
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

        # Read values from endpoints
        registry_set = OumanRegistrySet([SystemEndpoints, L1Endpoints])
        values = await client.get_values(registry_set)

        print(f"Outside temp: {values[SystemEndpoints.OUTSIDE_TEMPERATURE]} °C")
        print(f"L1 supply temp: {values[L1Endpoints.WATER_OUT_TEMPERATURE]} °C")

        # Set home/away mode
        await client.set_home_away(HomeAwayControl.HOME)

        # Set L1 operation mode
        await client.set_l1_operation_mode(OperationMode.AUTOMATIC)

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

| Registry | Description |
|----------|-------------|
| `SystemEndpoints` | System-wide settings (home/away, outside temp, etc.) |
| `L1Endpoints` | Primary heating circuit |
| `L1EndpointsWithRoomSensor` | L1 with room sensor (extends L1Endpoints) |
| `L2Endpoints` | Secondary heating circuit |
| `L2EndpointsWithRoomSensor` | L2 with room sensor (extends L2Endpoints) |

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
