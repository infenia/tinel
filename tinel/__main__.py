#!/usr/bin/env python3
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

"""This module provides the entry point for the Tinel command-line tool.

When executed as the main program, this module invokes the `main` function
from the `tinel.cli.main` module and exits with the returned status code.
This allows the Tinel package to be run as a standalone application.
"""

import sys

from .cli.main import main

if __name__ == "__main__":
    sys.exit(main())
