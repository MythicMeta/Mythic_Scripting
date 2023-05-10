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

Version 0.0.21-25 of the `mythic` package supports version 2.2.8+ of the Mythic project (reports as version "3").

Version 0.0.26 of the `mythic` package supports version 2.3+ of the Mythic project (reports as version "3").

Version 0.0.29-0.0.36 of the `mythic` package supports version 2.3+ of the Mythic project utilizing the new GraphQL endpoints and reports as version "3".
This will be the last version that supports the old mythic_rest interface. Starting with version 0.1.0, the `mythic` PyPi package will only support the new GraphQL interface and will report as version "4".

Version 0.1.0 of the `mythic` package supports version 3.0 of the Mythic project utilizing the new GraphQL endpoints.

# Information

The Jupyter Notebook container within Mythic provides many examples on how to use the package. 
The `mythic` package leverages async HTTP requests and WebSocket connections, so it's important to make sure your codebase is running asynchronously. 
