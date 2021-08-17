# Mythic Scripting Interface

The `mythic` package creates a way to programmatically interact and control a Mythic instance. Mythic is a Command and Control (C2) framework for Red Teaming. The code is on GitHub (https://github.com/its-a-feature/Mythic) and the Mythic project's documentation is on GitBooks (https://docs.mythic-c2.net).

## Installation

You can install the mythic scripting interface from PyPI:

```
pip install mythic
```

## How to use

Version 0.0.13 of the `mythic` package supports version 2.1.* of the Mythic project.

Version 0.0.15 of the `mythic` package supports version 2.2.1 of the Mythic project.

Version 0.0.20 of the `mythic` package supports version 2.2.6 of the Mythic project (reports as version "3").

Version 0.0.21-24 of the `mythic` package supports version 2.2.8+ of the Mythic project (reports as version "3").


```
from mythic import mythic_rest
mythic = mythic_rest.Mythic(
    username="mythic_admin",
    password="mythic_password",
    server_ip="192.168.205.151",
    server_port="7443",
    ssl=True,
    global_timeout=-1,
)
await mythic.login()
```

The Mythic documentation has a whole section on scripting examples (https://docs.mythic-c2.net/scripting) that are useful for how to leverage this package. The `mythic` package leverages async HTTP requests and WebSocket connections, so it's important to make sure your codebase is running asynchronously. An example stub to help with this is on the Mythic documentation scripting page.
