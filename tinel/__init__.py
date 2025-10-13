"""
Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
import sys

"""Tinel is a powerful and extensible command-line tool for Linux systems
that provides detailed information about hardware components. It gathers data
from various system commands and files, presenting it in a clear and
user-friendly format.
"""

from .interfaces import (
    HardwareInfo,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

__version__ = "0.1.0"
__author__ = "Infenia Private Limited"
__license__ = "Apache-2.0"

__all__ = [
    "HardwareInfo",
]
