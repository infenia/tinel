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

from unittest.mock import MagicMock, patch

import pytest

from tinel.hardware.network_analyzer import NetworkAnalyzer
from tinel.interfaces import CommandResult

# --- MOCK DATA ---

MOCK_IP_ADDR_OUTPUT = """
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 0c:de:ad:be:ef:00 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.10/24 brd 192.168.1.255 scope global dynamic noprefixroute eth0
       valid_lft 56872sec preferred_lft 56872sec
    inet6 fe80::dead:beef:feef:0/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
"""

MOCK_IP_LINK_OUTPUT = """
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    RX: bytes  packets  errors  dropped overrun mcast
    12345      100      0       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
    54321      200      0       0       0       0
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    link/ether 0c:de:ad:be:ef:00 brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped overrun mcast
    1000000    1000     5       1       0       50
    TX: bytes  packets  errors  dropped carrier collsns
    2000000    2000     10      2       0       0
"""

MOCK_IWCONFIG_OUTPUT = """
wlan0     IEEE 802.11  ESSID:"MyWiFi"
          Mode:Managed  Frequency:5.24 GHz  Access Point: 01:02:03:04:05:06
          Bit Rate=866.7 Mb/s   Tx-Power=22 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=70/70  Signal level=-40 dBm
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:0   Missed beacon:0
"""

MOCK_ETHTOOL_OUTPUT = """
NIC statistics:
     rx_packets: 1000
     tx_packets: 2000
     rx_bytes: 1000000
     tx_bytes: 2000000
"""

MOCK_MODINFO_OUTPUT = """
filename:       /lib/modules/5.15.0-48-generic/kernel/drivers/net/ethernet/intel/e1000e/e1000e.ko
version:        3.2.6-k
license:        GPL
description:    Intel(R) PRO/1000 Network Driver
author:         Intel Corporation, <e1000-devel@lists.sourceforge.net>
srcversion:     A8B7C6D5E4F3A2B1C0D9E8F
alias:          pci:v00008086d00001502sv*sd*bc*sc*i*
depends:
retpoline:      Y
intree:         Y
name:           e1000e
vermagic:       5.15.0-48-generic SMP mod_unload modversions
sig_id:         PKCS#7
signer:         buildd
sig_key:        ...
sig_hash:       SHA512
"""


@pytest.fixture
def mock_si():
    """Fixture for a mocked SystemInterface."""
    return MagicMock()


@pytest.fixture
def analyzer(mock_si):
    """Fixture for a NetworkAnalyzer with a mocked SystemInterface."""
    return NetworkAnalyzer(system_interface=mock_si)


class TestNetworkAnalyzer:
    @patch(
        "tinel.hardware.network_analyzer.NetworkAnalyzer._get_detailed_network_info",
        return_value={},
    )
    @patch(
        "tinel.hardware.network_analyzer.NetworkAnalyzer._get_wireless_info",
        return_value={},
    )
    @patch(
        "tinel.hardware.network_analyzer.NetworkAnalyzer._get_driver_info",
        return_value={},
    )
    @patch(
        "tinel.hardware.network_analyzer.NetworkAnalyzer._get_performance_metrics",
        return_value={},
    )
    def test_get_network_info_caching(
        self,
        mock_perf,
        mock_driver,
        mock_wireless,
        mock_detailed,
        analyzer,
        mock_si,
    ):
        """Test that the main get_network_info method caches results."""
        mock_si.run_command.return_value = CommandResult(
            success=True, stdout="data", stderr="", returncode=0
        )
        analyzer.get_network_info()
        analyzer.get_network_info()
        # The underlying _get_basic_network_info method should be called only once.
        # We check the number of calls to run_command made by it.
        assert mock_si.run_command.call_count == 2

    def test_get_basic_network_info(self, analyzer, mock_si):
        """Test the _get_basic_network_info method."""
        mock_si.run_command.side_effect = [
            CommandResult(True, MOCK_IP_ADDR_OUTPUT, "", 0),
            CommandResult(True, MOCK_IP_LINK_OUTPUT, "", 0),
        ]
        info = analyzer._get_basic_network_info()
        assert "interfaces" in info
        assert len(info["interfaces"]) == 2
        assert "interface_statistics" in info
        assert "lo" in info["interface_statistics"]

    def test_parse_ip_addr_output(self, analyzer):
        """Test parsing of 'ip addr' output."""

        parsed = analyzer._parse_ip_addr_output(MOCK_IP_ADDR_OUTPUT)
        assert len(parsed) == 2
        # Order might not be guaranteed, so check for existence
        lo_if = next((iface for iface in parsed if iface["name"] == "lo"), None)
        eth_if = next((iface for iface in parsed if iface["name"] == "eth0"), None)
        assert lo_if is not None
        assert eth_if is not None

        assert lo_if["state"] == "UNKNOWN"
        assert lo_if["mac"] == "00:00:00:00:00:00"
        assert len(lo_if["addresses"]) == 2

        assert eth_if["state"] == "UP"
        assert eth_if["mac"] == "0c:de:ad:be:ef:00"
        assert eth_if["addresses"][0]["address"] == "192.168.1.10/24"
        assert eth_if["addresses"][1]["address"] == "fe80::dead:beef:feef:0/64"

    def test_parse_ip_addr_output_no_details(self, analyzer):
        """Test parsing of 'ip addr' output with no details."""
        ip_addr_output = "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000"
        parsed = analyzer._parse_ip_addr_output(ip_addr_output)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "lo"

    def test_parse_ip_link_output(self, analyzer):
        """Test parsing of 'ip -s link' output."""
        parsed = analyzer._parse_ip_link_output(MOCK_IP_LINK_OUTPUT)
        stats = parsed["interface_statistics"]
        assert "lo" in stats
        assert "eth0" in stats
        assert stats["lo"]["rx"]["bytes"] == 12345
        assert stats["eth0"]["tx"]["packets"] == 2000
        assert stats["eth0"]["rx"]["errors"] == 5
        assert stats["eth0"]["tx"]["dropped"] == 2

    def test_parse_iwconfig_output(self, analyzer):
        """Test parsing of 'iwconfig' output."""
        parsed = analyzer._parse_iwconfig_output(MOCK_IWCONFIG_OUTPUT)
        assert len(parsed) == 1
        wlan0 = parsed[0]
        assert wlan0["name"] == "wlan0"
        assert wlan0["essid"] == "MyWiFi"
        assert wlan0["mode"] == "Managed"
        assert wlan0["frequency"] == "5.24 GHz"
        assert wlan0["access_point"] == "01:02:03:04:05:06"
        assert wlan0["bit_rate"] == "866.7 Mb/s"
        assert wlan0["signal_level"] == "-40 dBm"

    def test_parse_ethtool_output(self, analyzer):
        """Test parsing of 'ethtool -S' output."""
        parsed = analyzer._parse_ethtool_output(MOCK_ETHTOOL_OUTPUT)
        assert parsed["rx_packets"] == 1000
        assert parsed["tx_bytes"] == 2000000

    def test_get_driver_details(self, analyzer, mock_si):
        """Test parsing of 'modinfo' output."""
        mock_si.run_command.return_value = CommandResult(
            True, MOCK_MODINFO_OUTPUT, "", 0
        )
        details = analyzer._get_driver_details("e1000e")
        assert details["version"] == "3.2.6-k"
        assert details["license"] == "GPL"
        assert details["description"] == "Intel(R) PRO/1000 Network Driver"

    def test_get_interface_details(self, analyzer, mock_si):
        """Test gathering of interface details from /sys."""

        def read_file_side_effect(path):
            return {
                "/sys/class/net/eth0/type": "1",
                "/sys/class/net/eth0/speed": "1000",
                "/sys/class/net/eth0/duplex": "full",
                "/sys/class/net/eth0/address": "aa:bb:cc:dd:ee:ff",
                "/sys/class/net/eth0/flags": "0x1003",  # UP, BROADCAST, RUNNING
                "/sys/class/net/eth0/statistics/rx_bytes": "1234",
                "/sys/class/net/eth0/statistics/tx_bytes": "5678",
            }.get(path)

        mock_si.read_file.side_effect = read_file_side_effect
        mock_si.run_command.return_value = CommandResult(
            True, "rx_bytes\ntx_bytes", "", 0
        )

        details = analyzer._get_interface_details("eth0")
        assert details["name"] == "eth0"
        assert details["type"] == "ethernet"
        assert details["speed"] == 1000
        assert details["duplex"] == "full"
        assert details["address"] == "aa:bb:cc:dd:ee:ff"
        assert "UP" in details["decoded_flags"]
        assert "BROADCAST" in details["decoded_flags"]
        assert "statistics" in details
        assert details["statistics"]["rx_bytes"] == 1234

    def test_full_run_with_failures(self, analyzer, mock_si):
        """Test a full run where some commands fail."""
        with patch.object(analyzer, "logger") as mock_logger:

            def command_side_effect(cmd):
                if cmd == ["ip", "-s", "addr"]:
                    return CommandResult(True, MOCK_IP_ADDR_OUTPUT, "", 0)
                if cmd == ["ls", "/sys/class/net/"]:
                    return CommandResult(True, "lo eth0", "", 0)
                if cmd == ["ethtool", "-i", "eth0"]:
                    return CommandResult(True, "driver: e1000e", "", 0)
                # Fail other commands
                return CommandResult(False, "", "command not found", 1)

            mock_si.run_command.side_effect = command_side_effect
            mock_si.read_file.return_value = "1"  # for type

            info = analyzer.get_network_info()

            assert "interfaces" in info
            assert "wireless_interfaces" not in info  # iwconfig failed
            assert "ethtool_statistics" not in info  # ethtool -S failed
            assert "driver_info" in info
            assert info["driver_info"][0]["driver"] == "e1000e"
            assert "ip_link_error" in info  # ip -s link failed
            assert mock_logger.info.called

    def test_get_detailed_network_info_ls_fails(self, analyzer, mock_si):
        """Test that a failure to list /sys/class/net is handled."""
        with patch.object(analyzer, "logger") as mock_logger:
            mock_si.run_command.return_value = CommandResult(
                False, "", "Permission denied", 1
            )
            info = analyzer._get_detailed_network_info()
            assert "detailed_interfaces" not in info
            mock_logger.warning.assert_called_with(
                "Failed to list network interfaces in /sys/class/net/"
            )

    def test_parse_ip_addr_empty_output(self, analyzer):
        """Test parsing of empty 'ip addr' output."""
        parsed = analyzer._parse_ip_addr_output("")
        assert parsed == []

    def test_parse_ip_link_malformed_output(self, analyzer):
        """Test parsing of malformed 'ip -s link' output."""
        malformed_output = "1: lo: <LOOPBACK>\n  something unexpected"
        parsed = analyzer._parse_ip_link_output(malformed_output)
        assert "interface_statistics" in parsed
        assert "lo" in parsed["interface_statistics"]
        assert "rx" not in parsed["interface_statistics"]["lo"]

    def test_get_wireless_info_no_tools(self, analyzer, mock_si):
        """Test wireless info gathering when iwconfig and iw fail."""
        with patch.object(analyzer, "logger") as mock_logger:
            mock_si.run_command.return_value = CommandResult(False, "", "not found", 1)
            info = analyzer._get_wireless_info()
            assert info == {}
            assert mock_logger.info.call_count == 2

    def test_get_performance_metrics_no_tools(self, analyzer, mock_si):
        """Test performance metrics gathering when netstat and ethtool fail."""
        with patch.object(analyzer, "logger") as mock_logger:
            mock_si.run_command.return_value = CommandResult(False, "", "not found", 1)
            # Need to mock ls for the ethtool loop
            mock_si.run_command.side_effect = lambda cmd: {
                ("ls", "/sys/class/net/"): CommandResult(True, "eth0", "", 0)
            }.get(tuple(cmd), CommandResult(False, "", "not found", 1))

            info = analyzer._get_performance_metrics()
            assert "ethtool_statistics" not in info
            assert "netstat" not in info
            assert mock_logger.info.called

    def test_ip_addr_failure(self, analyzer, mock_si):
        """Test handling of ip addr command failure."""
        with patch.object(analyzer, "logger") as mock_logger:
            mock_si.run_command.return_value = CommandResult(
                False, "", "command failed", 1
            )
            info = analyzer._get_basic_network_info()
            assert "ip_addr_error" in info
            assert info["ip_addr_error"] == "command failed"
            mock_logger.warning.assert_called()

    def test_successful_iwconfig(self, analyzer, mock_si):
        """Test successful iwconfig command with wireless interfaces."""
        mock_si.run_command.side_effect = [
            CommandResult(True, MOCK_IWCONFIG_OUTPUT, "", 0),  # iwconfig
            CommandResult(False, "", "not found", 1),  # iw list fails
        ]
        info = analyzer._get_wireless_info()
        assert "iwconfig" in info
        assert "wireless_interfaces" in info
        assert len(info["wireless_interfaces"]) == 1
        assert info["wireless_interfaces"][0]["name"] == "wlan0"

    def test_successful_iw_list(self, analyzer, mock_si):
        """Test successful iw list command."""
        iw_output = "Wiphy phy0\nSupported interface modes:\n\t * IBSS\n\t * managed"
        mock_si.run_command.side_effect = [
            CommandResult(False, "", "not found", 1),  # iwconfig fails
            CommandResult(True, iw_output, "", 0),  # iw list succeeds
        ]
        info = analyzer._get_wireless_info()
        assert "iw_list" in info
        assert "wireless_capabilities" in info
        assert info["wireless_capabilities"]["raw"] == iw_output

    def test_successful_netstat(self, analyzer, mock_si):
        """Test successful netstat command."""
        netstat_output = "Iface      MTU    RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg\neth0      1500     1000      5      1      0     2000     10      2      0 BMRU"

        def command_side_effect(cmd):
            if cmd == ["netstat", "-i"]:
                return CommandResult(True, netstat_output, "", 0)
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "eth0", "", 0)
            return CommandResult(False, "", "not found", 1)

        mock_si.run_command.side_effect = command_side_effect
        info = analyzer._get_performance_metrics()
        assert "netstat" in info
        assert "interface_statistics" in info
        assert len(info["interface_statistics"]) == 1
        assert info["interface_statistics"][0]["iface"] == "eth0"

    def test_successful_ethtool_stats(self, analyzer, mock_si):
        """Test successful ethtool statistics gathering."""

        def command_side_effect(cmd):
            if cmd == ["netstat", "-i"]:
                return CommandResult(False, "", "not found", 1)
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "eth0\nwlan0", "", 0)
            if cmd == ["ethtool", "-S", "eth0"]:
                return CommandResult(True, MOCK_ETHTOOL_OUTPUT, "", 0)
            if cmd == ["ethtool", "-S", "wlan0"]:
                return CommandResult(True, MOCK_ETHTOOL_OUTPUT, "", 0)
            return CommandResult(False, "", "not found", 1)

        mock_si.run_command.side_effect = command_side_effect
        info = analyzer._get_performance_metrics()
        assert "ethtool_statistics" in info
        assert "eth0" in info["ethtool_statistics"]
        assert "wlan0" in info["ethtool_statistics"]
        assert info["ethtool_statistics"]["eth0"]["rx_packets"] == 1000

    def test_driver_with_details(self, analyzer, mock_si):
        """Test driver info gathering with modinfo details."""

        def command_side_effect(cmd):
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "eth0", "", 0)
            if cmd == ["ethtool", "-i", "eth0"]:
                return CommandResult(True, "driver: e1000e\nversion: 3.2.6", "", 0)
            if cmd == ["modinfo", "e1000e"]:
                return CommandResult(True, MOCK_MODINFO_OUTPUT, "", 0)
            return CommandResult(False, "", "not found", 1)

        mock_si.run_command.side_effect = command_side_effect
        info = analyzer._get_driver_info()
        assert "driver_info" in info
        assert len(info["driver_info"]) == 1
        assert info["driver_info"][0]["driver"] == "e1000e"
        assert "driver_details" in info["driver_info"][0]
        assert info["driver_info"][0]["driver_details"]["version"] == "3.2.6-k"

    def test_ethtool_no_driver_match(self, analyzer, mock_si):
        """Test ethtool without driver field in output."""
        with patch.object(analyzer, "logger") as mock_logger:
            mock_si.run_command.return_value = CommandResult(
                True, "version: 1.0", "", 0
            )
            driver = analyzer._get_interface_driver("eth0")
            assert driver is None
            mock_logger.info.assert_called_with(
                "Could not get driver for %s via ethtool.", "eth0"
            )

    def test_parse_iwconfig_with_empty_blocks(self, analyzer):
        """Test iwconfig parsing with empty blocks."""
        iwconfig_with_empty = MOCK_IWCONFIG_OUTPUT + "\n\n  \n\n"
        parsed = analyzer._parse_iwconfig_output(iwconfig_with_empty)
        assert len(parsed) == 1

    def test_parse_iwconfig_no_interface_name(self, analyzer):
        """Test iwconfig parsing with blocks that don't match the regex after splitting by double newlines."""
        # After splitting by '\n\n', we get blocks. For a block to be skipped,
        # it must not match the interface name regex r'^(\S+)'
        # This regex will fail to match if the block (after strip is called on the full output,
        # but before matching on individual blocks) starts with whitespace
        # Create output where a block starts with a space (not matching r'^(\S+)')
        invalid_output = "wlan0 valid\n\n   starts with space"
        parsed = analyzer._parse_iwconfig_output(invalid_output)
        # Should only parse the first valid block, skip the second
        assert len(parsed) == 1
        assert parsed[0]["name"] == "wlan0"

    def test_parse_iwconfig_no_wireless_extensions(self, analyzer):
        """Test iwconfig parsing with 'no wireless extensions' message."""
        no_wireless_output = "eth0      no wireless extensions."
        parsed = analyzer._parse_iwconfig_output(no_wireless_output)
        assert len(parsed) == 0

    def test_parse_netstat_short_output(self, analyzer):
        """Test netstat parsing with output that's too short."""
        short_output = "Iface"
        parsed = analyzer._parse_netstat_output(short_output)
        assert parsed == []

    def test_parse_netstat_valid_output(self, analyzer):
        """Test netstat parsing with valid output."""
        netstat_output = (
            "Iface      MTU    RX-OK\neth0      1500     1000\nwlan0     1500     2000"
        )
        parsed = analyzer._parse_netstat_output(netstat_output)
        assert len(parsed) == 2
        assert parsed[0]["iface"] == "eth0"
        assert parsed[0]["mtu"] == "1500"
        assert parsed[1]["iface"] == "wlan0"

    def test_parse_iwconfig_partial_fields(self, analyzer):
        """Test iwconfig parsing where some optional fields are missing."""
        # Test with an interface that has only some fields (no ESSID, Mode, etc)
        minimal_output = "wlan1     IEEE 802.11"
        parsed = analyzer._parse_iwconfig_output(minimal_output)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "wlan1"
        # These fields should not be present
        assert "essid" not in parsed[0]
        assert "mode" not in parsed[0]
        assert "frequency" not in parsed[0]
        assert "access_point" not in parsed[0]
        assert "bit_rate" not in parsed[0]
        assert "signal_level" not in parsed[0]

    def test_parse_iwconfig_truly_empty_block(self, analyzer):
        """Test iwconfig with a block that becomes empty after individual block processing."""
        # After split by '\n\n', if a block is just whitespace, the `if not block.strip():` should catch it
        # But the whole output is stripped first, so we need blocks that are separated but one is effectively empty
        output_with_empty = "wlan0 IEEE 802.11\n\n\n\nwlan1 IEEE 802.11"
        parsed = analyzer._parse_iwconfig_output(output_with_empty)
        # The empty blocks between the two interfaces should be skipped
        assert len(parsed) == 2
        assert parsed[0]["name"] == "wlan0"
        assert parsed[1]["name"] == "wlan1"

    def test_parse_iwconfig_all_fields_missing(self, analyzer):
        """Test iwconfig where all optional regex fields fail to match."""
        # Create an interface block where none of the optional fields have the expected format
        output_no_matches = """
wlan0     IEEE 802.11
          Mode-Not-Matching Frequency-Bad Access-Point-Bad
          Bit-Rate-Bad Signal-level-Bad"""
        parsed = analyzer._parse_iwconfig_output(output_no_matches)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "wlan0"
        # Verify none of the optional fields were matched
        assert "essid" not in parsed[0]
        assert "mode" not in parsed[0]
        assert "frequency" not in parsed[0]
        assert "access_point" not in parsed[0]
        assert "bit_rate" not in parsed[0]
        assert "signal_level" not in parsed[0]

    def test_parse_ip_addr_no_state_match(self, analyzer):
        """Test ip addr parsing where state is not in the expected format."""
        ip_addr_no_state = (
            "1: lo: <LOOPBACK,UP> mtu 65536\n    link/loopback 00:00:00:00:00:00"
        )
        parsed = analyzer._parse_ip_addr_output(ip_addr_no_state)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "lo"
        assert "state" not in parsed[0]

    def test_parse_ip_addr_no_mac_match(self, analyzer):
        """Test ip addr parsing where MAC address doesn't match expected format."""
        ip_addr_no_mac = "1: lo: <LOOPBACK,UP> state UNKNOWN\n    linktype something"
        parsed = analyzer._parse_ip_addr_output(ip_addr_no_mac)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "lo"
        assert "mac" not in parsed[0]

    def test_parse_ip_addr_no_ip_match(self, analyzer):
        """Test ip addr with malformed IP addresses."""
        ip_addr_bad_ip = "1: eth0: <BROADCAST> state UP\n    link/ether aa:bb:cc:dd:ee:ff\n    inet not-an-ip scope global\n    inet6 not-an-ipv6 scope link"
        parsed = analyzer._parse_ip_addr_output(ip_addr_bad_ip)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "eth0"
        assert len(parsed[0]["addresses"]) == 0  # No valid IPs parsed

    def test_get_interface_details_no_type(self, analyzer, mock_si):
        """Test interface details when type file is not available."""
        mock_si.read_file.return_value = None
        mock_si.run_command.return_value = CommandResult(False, "", "", 1)
        details = analyzer._get_interface_details("eth0")
        assert details["name"] == "eth0"
        assert "type" not in details

    def test_get_interface_details_no_flags(self, analyzer, mock_si):
        """Test interface details when flags file is not available."""

        def read_file_side_effect(path):
            if "/flags" in path:
                return None
            if "/type" in path:
                return "1"
            return None

        mock_si.read_file.side_effect = read_file_side_effect
        mock_si.run_command.return_value = CommandResult(False, "", "", 1)
        details = analyzer._get_interface_details("eth0")
        assert details["name"] == "eth0"
        assert "flags" not in details
        assert "decoded_flags" not in details

    def test_get_interface_details_no_statistics(self, analyzer, mock_si):
        """Test interface details when statistics files are not available."""

        def read_file_side_effect(path):
            if "/statistics/" in path:
                return None
            if "/type" in path:
                return "1"
            return None

        mock_si.read_file.side_effect = read_file_side_effect
        mock_si.run_command.return_value = CommandResult(
            True, "rx_bytes\ntx_bytes", "", 0
        )
        details = analyzer._get_interface_details("eth0")
        assert details["name"] == "eth0"
        assert "statistics" not in details

    def test_get_detailed_network_info_no_interfaces(self, analyzer, mock_si):
        """Test _get_detailed_network_info when only loopback interface exists."""
        mock_si.run_command.return_value = CommandResult(True, "lo", "", 0)
        info = analyzer._get_detailed_network_info()
        # Should return empty dict since lo is skipped and interfaces list remains empty
        assert "detailed_interfaces" not in info

    def test_get_driver_info_no_drivers(self, analyzer, mock_si):
        """Test _get_driver_info when no drivers can be retrieved."""

        def command_side_effect(cmd):
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0", "", 0)
            if cmd == ["ethtool", "-i", "eth0"]:
                return CommandResult(False, "", "not found", 1)
            return CommandResult(False, "", "", 1)

        mock_si.run_command.side_effect = command_side_effect
        info = analyzer._get_driver_info()
        # Should return empty dict since driver_info list remains empty
        assert "driver_info" not in info

    def test_get_performance_metrics_no_ethtool_stats(self, analyzer, mock_si):
        """Test _get_performance_metrics when ethtool commands all fail."""

        def command_side_effect(cmd):
            if cmd == ["netstat", "-i"]:
                return CommandResult(False, "", "not found", 1)
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0", "", 0)
            if cmd[0] == "ethtool":
                return CommandResult(False, "", "not found", 1)
            return CommandResult(False, "", "", 1)

        with patch.object(analyzer, "logger") as mock_logger:
            mock_si.run_command.side_effect = command_side_effect
            info = analyzer._get_performance_metrics()
            # Should return empty dict since ethtool_stats remains empty
            assert "ethtool_statistics" not in info

    def test_parse_ip_link_no_interface_match(self, analyzer):
        """Test _parse_ip_link_output with lines that don't match interface pattern."""
        malformed = "Something that doesn't match\n  RX: bytes  packets\n  12345 100"
        parsed = analyzer._parse_ip_link_output(malformed)
        assert parsed == {"interface_statistics": {}}

    def test_parse_ip_link_incomplete_rx_values(self, analyzer):
        """Test _parse_ip_link_output with incomplete RX statistics."""
        incomplete_rx = (
            "1: eth0: <BROADCAST>\n    RX: bytes  packets  errors\n    12345 100"
        )
        parsed = analyzer._parse_ip_link_output(incomplete_rx)
        # RX stats should not be added since len(values) < 6
        assert "rx" not in parsed["interface_statistics"].get("eth0", {})

    def test_parse_ip_link_incomplete_tx_values(self, analyzer):
        """Test _parse_ip_link_output with incomplete TX statistics."""
        incomplete_tx = "1: eth0: <BROADCAST>\n    RX: bytes  packets  errors  dropped  overrun  mcast\n    12345 100 0 0 0 0\n    TX: bytes  packets\n    54321 200"
        parsed = analyzer._parse_ip_link_output(incomplete_tx)
        # TX stats should not be added since len(values) < 6
        assert "tx" not in parsed["interface_statistics"].get("eth0", {})

    def test_parse_ethtool_output_no_colon(self, analyzer):
        """Test _parse_ethtool_output with lines that don't contain colons."""
        no_colon = "NIC statistics:\nsome_stat 12345\nother_line"
        parsed = analyzer._parse_ethtool_output(no_colon)
        assert parsed == {}

    def test_parse_ethtool_output_non_numeric(self, analyzer):
        """Test _parse_ethtool_output with non-numeric values."""
        non_numeric = "NIC statistics:\n     stat1: not_a_number\n     stat2: abc"
        parsed = analyzer._parse_ethtool_output(non_numeric)
        assert parsed == {}

    def test_get_wireless_info_iwconfig_empty_stdout(self, analyzer, mock_si):
        """Test _get_wireless_info when iwconfig succeeds but returns empty output."""
        mock_si.run_command.side_effect = [
            CommandResult(True, "", "", 0),  # iwconfig with empty stdout
            CommandResult(False, "", "not found", 1),  # iw fails
        ]
        info = analyzer._get_wireless_info()
        # Should not add iwconfig or wireless_interfaces since stdout is empty
        assert "iwconfig" not in info
        assert "wireless_interfaces" not in info

    def test_parse_ip_addr_no_interface_match(self, analyzer):
        """Test _parse_ip_addr_output with lines that don't match interface pattern."""
        no_match = "Some random line\n  Another line without interface format"
        parsed = analyzer._parse_ip_addr_output(no_match)
        assert parsed == []

    def test_parse_netstat_insufficient_values(self, analyzer):
        """Test _parse_netstat_output where values list is shorter than headers."""
        insufficient = "Iface      MTU    RX-OK RX-ERR\neth0      1500"
        parsed = analyzer._parse_netstat_output(insufficient)
        # Should not add this interface since len(values) < len(headers)
        assert len(parsed) == 0

    def test_get_detailed_network_info_with_loopback_and_interface(
        self,
        analyzer,
        mock_si,
    ):
        """Test _get_detailed_network_info iterating through multiple interfaces including lo."""

        def command_side_effect(cmd):
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0 eth1", "", 0)
            return CommandResult(True, "", "", 0)

        def read_file_side_effect(path):
            if "/type" in path:
                return "1"
            return None

        mock_si.run_command.side_effect = command_side_effect
        mock_si.read_file.side_effect = read_file_side_effect
        info = analyzer._get_detailed_network_info()
        # Should have 2 interfaces (eth0, eth1), lo should be skipped
        assert "detailed_interfaces" in info
        assert len(info["detailed_interfaces"]) == 2

    def test_get_wireless_info_iwconfig_success_iw_success(self, analyzer, mock_si):
        """Test _get_wireless_info when both iwconfig and iw succeed."""
        iw_output = "Wiphy phy0\n\tSupported modes"
        mock_si.run_command.side_effect = [
            CommandResult(True, MOCK_IWCONFIG_OUTPUT, "", 0),  # iwconfig succeeds
            CommandResult(True, iw_output, "", 0),  # iw succeeds
        ]
        info = analyzer._get_wireless_info()
        assert "iwconfig" in info
        assert "wireless_interfaces" in info
        assert "iw_list" in info
        assert "wireless_capabilities" in info

    def test_get_driver_info_multiple_interfaces(self, analyzer, mock_si):
        """Test _get_driver_info with multiple interfaces, some with drivers."""

        def command_side_effect(cmd):
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0 eth1 wlan0", "", 0)
            if cmd == ["ethtool", "-i", "eth0"]:
                return CommandResult(True, "driver: e1000e", "", 0)
            if cmd == ["ethtool", "-i", "eth1"]:
                return CommandResult(False, "", "no driver", 1)
            if cmd == ["ethtool", "-i", "wlan0"]:
                return CommandResult(True, "driver: iwlwifi", "", 0)
            if cmd == ["modinfo", "e1000e"]:
                return CommandResult(True, "version: 1.0", "", 0)
            if cmd == ["modinfo", "iwlwifi"]:
                return CommandResult(True, "version: 2.0", "", 0)
            return CommandResult(False, "", "", 1)

        mock_si.run_command.side_effect = command_side_effect
        info = analyzer._get_driver_info()
        # Should have driver info for eth0 and wlan0, skip lo and eth1
        assert "driver_info" in info
        assert len(info["driver_info"]) == 2

    def test_get_performance_metrics_mixed_ethtool(self, analyzer, mock_si):
        """Test _get_performance_metrics with some ethtool successes and failures."""

        def command_side_effect(cmd):
            if cmd == ["netstat", "-i"]:
                return CommandResult(False, "", "not found", 1)
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0 eth1", "", 0)
            if cmd == ["ethtool", "-S", "eth0"]:
                return CommandResult(True, MOCK_ETHTOOL_OUTPUT, "", 0)
            if cmd == ["ethtool", "-S", "eth1"]:
                return CommandResult(False, "", "not found", 1)
            return CommandResult(False, "", "", 1)

        with patch.object(analyzer, "logger"):
            mock_si.run_command.side_effect = command_side_effect
            info = analyzer._get_performance_metrics()
            # Should have ethtool stats for eth0 only
            assert "ethtool_statistics" in info
            assert "eth0" in info["ethtool_statistics"]
            assert "eth1" not in info["ethtool_statistics"]

    def test_get_driver_details_empty_modinfo(self, analyzer, mock_si):
        """Test _get_driver_details when modinfo returns lines without colons."""
        modinfo_no_colon = "some_module.ko\nNo colons here\nAnother line"
        mock_si.run_command.return_value = CommandResult(True, modinfo_no_colon, "", 0)
        details = analyzer._get_driver_details("test_driver")
        # Should return empty dict since no lines have colons
        assert details == {}

    def test_get_detailed_network_info_skip_first_continue_second(
        self,
        analyzer,
        mock_si,
    ):
        """Test loop where first interface returns no info, second returns info."""

        call_count = [0]

        def command_side_effect(cmd):
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0 eth1", "", 0)
            return CommandResult(True, "", "", 0)

        def read_file_side_effect(path):
            # First call (eth0) returns None for all files
            # Second call (eth1) returns valid type
            call_count[0] += 1
            if "eth1" in path and "/type" in path:
                return "1"
            return None

        mock_si.run_command.side_effect = command_side_effect
        mock_si.read_file.side_effect = read_file_side_effect
        info = analyzer._get_detailed_network_info()
        # Should skip lo, eth0 returns empty dict (not added), eth1 returns valid info
        assert "detailed_interfaces" in info
        assert len(info["detailed_interfaces"]) >= 1

    def test_get_driver_info_skip_then_add(self, analyzer, mock_si):
        """Test loop where first has no driver, second has driver."""
        call_count = [0]

        def command_side_effect(cmd):
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0 eth1", "", 0)
            if cmd == ["ethtool", "-i", "eth0"]:
                # First interface: no driver
                return CommandResult(False, "", "no driver", 1)
            if cmd == ["ethtool", "-i", "eth1"]:
                # Second interface: has driver
                return CommandResult(True, "driver: virtio", "", 0)
            if cmd == ["modinfo", "virtio"]:
                return CommandResult(True, "version: 1.0", "", 0)
            return CommandResult(False, "", "", 1)

        mock_si.run_command.side_effect = command_side_effect
        info = analyzer._get_driver_info()
        # Should skip lo and eth0, add eth1
        assert "driver_info" in info
        assert len(info["driver_info"]) == 1
        assert info["driver_info"][0]["interface"] == "eth1"

    def test_get_performance_metrics_skip_then_add_ethtool(self, analyzer, mock_si):
        """Test ethtool loop where first fails, second succeeds."""

        def command_side_effect(cmd):
            if cmd == ["netstat", "-i"]:
                return CommandResult(False, "", "not found", 1)
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "lo eth0 eth1", "", 0)
            if cmd == ["ethtool", "-S", "eth0"]:
                # First interface: ethtool fails
                return CommandResult(False, "", "no stats", 1)
            if cmd == ["ethtool", "-S", "eth1"]:
                # Second interface: ethtool succeeds
                return CommandResult(True, MOCK_ETHTOOL_OUTPUT, "", 0)
            return CommandResult(False, "", "", 1)

        with patch.object(analyzer, "logger"):
            mock_si.run_command.side_effect = command_side_effect
            info = analyzer._get_performance_metrics()
            # Should skip lo and eth0, add stats for eth1
            assert "ethtool_statistics" in info
            assert "eth0" not in info["ethtool_statistics"]
            assert "eth1" in info["ethtool_statistics"]

    def test_get_wireless_info_iwconfig_success_then_iw_fail(self, analyzer, mock_si):
        """Test wireless info where iwconfig succeeds but iw fails after success check."""
        mock_si.run_command.side_effect = [
            CommandResult(True, MOCK_IWCONFIG_OUTPUT, "", 0),  # iwconfig succeeds
            CommandResult(False, "", "not found", 1),  # iw fails
        ]
        with patch.object(analyzer, "logger") as mock_logger:
            info = analyzer._get_wireless_info()
            # Should have iwconfig data but not iw data
            assert "iwconfig" in info
            assert "wireless_interfaces" in info
            assert "iw_list" not in info
            assert "wireless_capabilities" not in info

    def test_get_basic_network_info_ip_addr_fail_no_stderr(self, analyzer, mock_si):
        """Test _get_basic_network_info with ip addr failure and no stderr."""
        mock_si.run_command.side_effect = [
            CommandResult(False, "", "", 1),
            CommandResult(True, "", "", 0),
        ]
        info = analyzer._get_basic_network_info()
        assert "ip_addr_error" in info
        assert info["ip_addr_error"] == "Failed to run ip addr"

    def test_get_detailed_network_info_empty_interface_info(self, analyzer, mock_si):
        """Test _get_detailed_network_info when _get_interface_details returns empty."""
        mock_si.run_command.return_value = CommandResult(True, "eth0", "", 0)
        with patch.object(analyzer, "_get_interface_details", return_value=None):
            info = analyzer._get_detailed_network_info()
            assert "detailed_interfaces" not in info

    def test_get_driver_info_no_driver_details(self, analyzer, mock_si):
        """Test _get_driver_info when driver is found but no details."""
        mock_si.run_command.side_effect = [
            CommandResult(True, "eth0", "", 0),
            CommandResult(True, "driver: mydriver", "", 0),
            CommandResult(True, "", "", 0),  # modinfo returns empty
        ]
        with patch.object(analyzer, "_get_driver_details", return_value={}):
            info = analyzer._get_driver_info()
            assert "driver_info" in info
            assert "driver_details" not in info["driver_info"][0]

    def test_parse_ip_addr_output_no_current_interface(self, analyzer):
        """Test _parse_ip_addr_output with a line that doesn't start a new interface."""
        output = "  inet 127.0.0.1/8 scope host lo"
        parsed = analyzer._parse_ip_addr_output(output)
        assert not parsed

    def test_get_interface_details_unknown_type(self, analyzer, mock_si):
        """Test _get_interface_details with an unknown interface type."""

        def read_file_side_effect(path):
            if path.endswith("/type"):
                return "999"
            return None

        mock_si.read_file.side_effect = read_file_side_effect
        mock_si.run_command.return_value = CommandResult(False, "", "", 1)
        details = analyzer._get_interface_details("eth0")
        assert details["type"] == "unknown (999)"

    def test_get_driver_info_no_driver(self, analyzer, mock_si):
        """Test _get_driver_info when ethtool fails to find a driver."""
        mock_si.run_command.side_effect = [
            CommandResult(True, "eth0", "", 0),
            CommandResult(False, "", "error", 1),
        ]
        info = analyzer._get_driver_info()
        assert "driver_info" not in info

    def test_get_interface_details_no_stats(self, analyzer, mock_si):
        """Test _get_interface_details when ls on statistics path fails."""

        def read_sys_file_mock(file):
            return None

        with patch.object(analyzer.system, "read_file", side_effect=read_sys_file_mock):
            analyzer.system.run_command.return_value = CommandResult(
                success=False, stdout="", stderr="error", returncode=1
            )
            interface_info = analyzer._get_interface_details("eth0")
            assert "statistics" not in interface_info

    def test_parse_ip_addr_output_no_state(self, analyzer):
        """Test parsing ip addr output without a state field."""
        ip_addr_output = "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel group default qlen 1000"
        parsed = analyzer._parse_ip_addr_output(ip_addr_output)
        assert "state" not in parsed[0]

    def test_get_basic_network_info_ip_link_fail_no_stderr(self, analyzer, mock_si):
        """Test _get_basic_network_info with ip link failure and no stderr."""
        mock_si.run_command.side_effect = [
            CommandResult(True, "", "", 0),
            CommandResult(False, "", "", 1),
        ]
        info = analyzer._get_basic_network_info()
        assert "ip_link_error" in info
        assert info["ip_link_error"] == "Failed to run ip -s link"

    def test_get_detailed_network_info_interface_info_is_false(self, analyzer, mock_si):
        """Test _get_detailed_network_info when _get_interface_details returns a falsy value."""
        mock_si.run_command.return_value = CommandResult(True, "eth0", "", 0)
        with patch.object(analyzer, "_get_interface_details", return_value={}):
            info = analyzer._get_detailed_network_info()
            assert "detailed_interfaces" not in info

    def test_get_driver_info_driver_found_no_details(self, analyzer, mock_si):
        """Test _get_driver_info when a driver is found but modinfo returns no details."""

        def command_side_effect(cmd):
            if cmd == ["ls", "/sys/class/net/"]:
                return CommandResult(True, "eth0", "", 0)
            if cmd == ["ethtool", "-i", "eth0"]:
                return CommandResult(True, "driver: a_driver", "", 0)
            if cmd == ["modinfo", "a_driver"]:
                return CommandResult(True, "", "", 0)  # Empty output from modinfo
            return CommandResult(False, "", "", 1)

        mock_si.run_command.side_effect = command_side_effect
        info = analyzer._get_driver_info()
        assert "driver_info" in info
        assert len(info["driver_info"]) == 1
        assert "driver_details" not in info["driver_info"][0]

    def test_parse_ip_addr_output_continues_after_no_match(self, analyzer):
        """Test that parsing continues after a line that doesn't match."""
        output = "1: lo: <LOOPBACK>\n    some other line\n2: eth0: <BROADCAST>"
        parsed = analyzer._parse_ip_addr_output(output)
        assert len(parsed) == 2
        assert parsed[0]["name"] == "lo"
        assert parsed[1]["name"] == "eth0"

    def test_get_performance_metrics_ls_fails(self, analyzer, mock_si):
        """Test _get_performance_metrics when ls fails."""
        mock_si.run_command.side_effect = [
            CommandResult(True, "some output", "", 0),  # netstat
            CommandResult(False, "", "error", 1),  # ls
        ]
        info = analyzer._get_performance_metrics()
        assert "ethtool_statistics" not in info

    def test_get_driver_info_ls_fails(self, analyzer, mock_si):
        """Test _get_driver_info when ls fails."""
        mock_si.run_command.return_value = CommandResult(False, "", "error", 1)
        info = analyzer._get_driver_info()
        assert "driver_info" not in info

    def test_get_driver_info_ls_empty(self, analyzer, mock_si):
        """Test _get_driver_info when ls returns empty output."""
        mock_si.run_command.return_value = CommandResult(True, "", "", 0)
        info = analyzer._get_driver_info()
        assert "driver_info" not in info

    def test_get_driver_info_only_lo(self, analyzer, mock_si):
        """Test _get_driver_info when only 'lo' interface is present."""
        mock_si.run_command.return_value = CommandResult(True, "lo", "", 0)
        info = analyzer._get_driver_info()
        assert "driver_info" not in info

    def test_parse_ip_addr_malformed_interface_line(self, analyzer):
        """Test parsing ip addr output with a malformed interface line."""
        output = "this is not a valid interface line\n  inet 127.0.0.1/8"
        parsed = analyzer._parse_ip_addr_output(output)
        assert not parsed
