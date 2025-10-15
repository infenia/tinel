# -*- coding: utf-8 -*-
"""
This module defines the data structures for representing kernel configurations.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class KernelConfigOption:
    """Represents a single kernel configuration option."""

    name: str
    value: str
    recommended: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Validates the KernelConfigOption fields after initialization.

        Raises:
            ValueError: If the name is empty or the value is invalid.
        """
        if not self.name:
            raise ValueError("KernelConfigOption name cannot be empty")
        if self.value not in ("y", "n", "m"):
            raise ValueError(f"Invalid value for {self.name}: {self.value}")


@dataclass
class KernelConfig:
    """Represents a collection of kernel configuration options."""

    options: List[KernelConfigOption]

    def get_option(self, name: str) -> Optional[KernelConfigOption]:
        """Get a specific option by name."""
        for option in self.options:
            if option.name == name:
                return option
        return None
