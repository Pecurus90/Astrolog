"""How the night will be, from the services that forecast it (contract: docs/domini/meteo.md).
It sits beside the spine and neither knows the other, so a scan without network goes on."""

from collections.abc import Callable
from typing import Any

# The network call each writer receives, so tests pass a fake and never leave the machine.
type Fetch = Callable[[str], Any]
