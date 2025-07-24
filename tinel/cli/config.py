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


import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class CLIConfig:
    """Configuration object for CLI operations."""
    
    format_type: str = 'text'
    use_color: bool = True
    verbose: int = 0
    quiet: bool = False
    config_file: Optional[str] = None
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'CLIConfig':
        """Create configuration from parsed arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            CLIConfig instance
        """
        return cls(
            format_type=args.format,
            use_color=not args.no_color,
            verbose=args.verbose,
            quiet=args.quiet,
            config_file=getattr(args, 'config', None)
        )
    
    def validate(self) -> None:
        """Validate configuration consistency.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if self.verbose > 0 and self.quiet:
            raise ValueError("Cannot use both verbose and quiet modes together")
        
        if self.verbose < 0:
            raise ValueError("Verbosity level cannot be negative")
        
        if self.verbose > 3:
            raise ValueError("Maximum verbosity level is 3")
        
        valid_formats = ['text', 'json', 'yaml', 'csv']
        if self.format_type not in valid_formats:
            raise ValueError(f"Invalid format '{self.format_type}'. Valid formats: {', '.join(valid_formats)}")
    
    @property
    def should_use_color(self) -> bool:
        """Determine if color should be used based on configuration and environment."""
        import os
        import sys
        
        # Respect NO_COLOR environment variable (https://no-color.org/)
        if os.environ.get('NO_COLOR'):
            return False
        
        # Force color if FORCE_COLOR is set
        if os.environ.get('FORCE_COLOR'):
            return True
        
        # Use color if explicitly enabled and stdout is a TTY
        return self.use_color and hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    @property
    def log_level(self) -> str:
        """Get appropriate log level based on verbosity."""
        if self.quiet:
            return 'ERROR'
        elif self.verbose == 0:
            return 'WARNING'
        elif self.verbose == 1:
            return 'INFO'
        else:  # verbose >= 2
            return 'DEBUG'