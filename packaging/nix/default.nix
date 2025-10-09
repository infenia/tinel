{ lib
, python3
, fetchFromGitHub
, util-linux
, pciutils
, usbutils
, lshw
, dmidecode
, smartmontools
, hdparm
, ethtool
, iproute2
, procps
, installShellFiles
}:

python3.pkgs.buildPythonApplication rec {
  pname = "tinel";
  version = "0.1.0";
  format = "pyproject";

  src = fetchFromGitHub {
    owner = "infenia";
    repo = "tinel";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nativeBuildInputs = with python3.pkgs; [
    setuptools
    wheel
    build
    installShellFiles
  ];

  propagatedBuildInputs = with python3.pkgs; [
    psutil
    cryptography
    pyyaml
  ];

  buildInputs = [
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
  ];

  # Skip tests during build (they require system access)
  doCheck = false;

  postInstall = ''
    # Install shell completions
    installShellCompletion --cmd tinel \
      --bash packaging/debian/bash_completion

    # Install man page
    installManPage packaging/debian/tinel.1

    # Install desktop file
    mkdir -p $out/share/applications
    cp packaging/debian/tinel.desktop $out/share/applications/

    # Create wrapper script that includes system tools in PATH
    wrapProgram $out/bin/tinel \
      --prefix PATH : ${lib.makeBinPath [
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
      ]}
  '';

  meta = with lib; {
    description = "Next-generation Linux system analysis platform";
    longDescription = ''
      Tinel is an advanced open-source platform designed to control, optimize,
      and analyze Linux-based systems using AI and LLMs. It provides comprehensive
      hardware information gathering, system diagnostics, and performance analysis.

      Key features:
      * Hardware analysis and detection
      * System performance monitoring
      * AI-powered diagnostics
      * Model Context Protocol (MCP) server
      * RESTful API interface
      * Comprehensive reporting
    '';
    homepage = "https://github.com/infenia/tinel";
    license = licenses.asl20;
    maintainers = with maintainers; [ ];
    platforms = platforms.linux;
    mainProgram = "tinel";
  };
}

# Usage examples:
#
# To build and install:
#   nix-env -iA nixpkgs.tinel
#
# To run directly:
#   nix run nixpkgs#tinel -- --help
#
# To use in a shell:
#   nix shell nixpkgs#tinel
#
# For development:
#   nix develop