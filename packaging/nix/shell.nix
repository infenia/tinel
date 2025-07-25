{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "tinel-dev-shell";

  buildInputs = with pkgs; [
    # Python and development tools
    python312
    python312Packages.pip
    python312Packages.virtualenv
    python312Packages.build
    python312Packages.twine
    
    # Development dependencies
    python312Packages.pytest
    python312Packages.pytest-cov
    python312Packages.black
    python312Packages.ruff
    python312Packages.mypy
    
    # System utilities for hardware detection
    util-linux
    pciutils
    usbutils
    lshw
    dmidecode
    smartmontools
    hdparm
    ethtool
    iproute2
    procps
    
    # Build tools
    git
    curl
    wget
    
    # Documentation tools
    python312Packages.pdoc
    
    # Container tools
    docker
    docker-compose
    
    # Package building tools
    rpm
    dpkg
    
    # Nix development tools
    nixpkgs-fmt
    nix-prefetch-git
  ];

  shellHook = ''
    echo "🔧 Tinel development environment activated!"
    echo ""
    echo "Available commands:"
    echo "  python -m tinel --help    # Run Tinel directly"
    echo "  python -m pytest         # Run tests"
    echo "  python -m ruff check .    # Lint code"
    echo "  python -m black .         # Format code"
    echo "  python -m mypy tinel      # Type check"
    echo "  python -m build           # Build package"
    echo ""
    echo "System tools available:"
    echo "  lscpu, lspci, lsusb, lshw, dmidecode"
    echo ""
    
    # Set up Python environment
    export PYTHONPATH="$PWD:$PYTHONPATH"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
      echo "Creating Python virtual environment..."
      python -m venv .venv
      source .venv/bin/activate
      pip install -e ".[dev]"
    else
      echo "Activating existing virtual environment..."
      source .venv/bin/activate
    fi
    
    echo "✅ Ready for development!"
  '';

  # Environment variables
  TINEL_LOG_LEVEL = "DEBUG";
  TINEL_DEV_MODE = "1";
}