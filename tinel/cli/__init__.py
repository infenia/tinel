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

from .main import main
from .parser import create_argument_parser

"""This package contains the command-line interface (CLI) for Tinel.

It is responsible for parsing command-line arguments, routing commands to their
respective handlers, and formatting the output for the user. The main entry
point for the CLI is the `main` function in the `main` module.
"""


__all__ = ["create_argument_parser", "main"]
