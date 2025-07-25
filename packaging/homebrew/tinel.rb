class Tinel < Formula
  desc "Next-generation Linux system analysis platform"
  homepage "https://github.com/infenia/tinel"
  url "https://github.com/infenia/tinel/archive/v0.1.0.tar.gz"
  sha256 "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890"
  license "Apache-2.0"
  head "https://github.com/infenia/tinel.git", branch: "main"

  # Dependencies
  depends_on "python@3.12"
  depends_on "util-linux" if OS.linux?
  depends_on "pciutils" if OS.linux?
  depends_on "usbutils" if OS.linux?
  depends_on "lshw" if OS.linux?

  # Python dependencies will be installed via pip
  resource "psutil" do
    url "https://files.pythonhosted.org/packages/90/c7/6dc0a455d111f68ee43f27793971cf03fe29b6ef972042549db29eec39a95/psutil-5.9.5.tar.gz"
    sha256 "5410638e4df39c54d957fc51ce03048acd8e6d60abc0f5107af51e5fb566eb3c"
  end

  resource "cryptography" do
    url "https://files.pythonhosted.org/packages/13/9a/2a2d8d851d81a8ecad2cd80c5d95c16ef3b42ea8a7e34a7e10b0c2a67f8cf/cryptography-41.0.7.tar.gz"
    sha256 "13f93ce9bea8016c253b34afc6bd6a75993e5c40672ed5405a9c832f0d4a00bc"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/cd/e5/af35f7ea75cf72f2cd079c95ee16797de7cd71f29ea7c68ae5ce7be1eda02/PyYAML-6.0.1.tar.gz"
    sha256 "bfdf460b1736c775f2ba9f6a92bca30bc2095067b8a9d77876d1fad6cc3b4a43"
  end

  # Build and install
  def install
    # Create virtual environment
    venv = virtualenv_create(libexec, "python3.12")
    
    # Install Python dependencies
    venv.pip_install resources
    
    # Install Tinel
    venv.pip_install_and_link buildpath
    
    # Create shell completion
    generate_completions_from_executable(bin/"tinel", shells: [:bash, :zsh], shell_parameter_format: :click)
  end

  # Service configuration
  service do
    run [opt_bin/"tinel", "server"]
    working_dir var/"lib/tinel"
    log_path var/"log/tinel/tinel.log"
    error_log_path var/"log/tinel/tinel-error.log"
    environment_variables TINEL_CONFIG: etc/"tinel/config.yaml"
  end

  def post_install
    # Create configuration directory
    (etc/"tinel").mkpath
    
    # Create data directories
    (var/"lib/tinel").mkpath
    (var/"log/tinel").mkpath
    
    # Install default configuration
    unless (etc/"tinel/config.yaml").exist?
      (etc/"tinel/config.yaml").write <<~EOS
        # Tinel Homebrew Configuration
        server:
          host: "127.0.0.1"
          port: 8080
          workers: 2
          debug: false

        logging:
          level: "INFO"
          file: "#{var}/log/tinel/tinel.log"
          max_size: "10MB"
          backup_count: 3

        hardware:
          cpu: true
          memory: true
          storage: true
          network: true
          gpu: true

        cache:
          directory: "#{var}/lib/tinel/cache"
          ttl: 300
          max_size: "50MB"

        security:
          require_auth: false
      EOS
    end
  end

  def caveats
    <<~EOS
      Tinel has been installed with Homebrew!
      
      Configuration file: #{etc}/tinel/config.yaml
      Data directory: #{var}/lib/tinel
      Log directory: #{var}/log/tinel

      To start the Tinel server:
        brew services start tinel

      To run Tinel manually:
        tinel --help
        tinel hardware
        tinel server

      Note: Some hardware detection features may require additional
      system utilities that are not available on macOS.
    EOS
  end

  test do
    # Basic functionality test
    system "#{bin}/tinel", "--version"
    system "#{bin}/tinel", "--help"
    
    # Test configuration loading
    assert_match "Tinel", shell_output("#{bin}/tinel --version")
    
    # Test Python import
    system libexec/"bin/python", "-c", "import tinel; print(tinel.__version__)"
  end
end