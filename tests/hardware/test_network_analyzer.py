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

import pytest
from unittest.mock import MagicMock, patch, call
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

    @patch('tinel.hardware.network_analyzer.NetworkAnalyzer._get_detailed_network_info', return_value={})
    @patch('tinel.hardware.network_analyzer.NetworkAnalyzer._get_wireless_info', return_value={})
    @patch('tinel.hardware.network_analyzer.NetworkAnalyzer._get_driver_info', return_value={})
    @patch('tinel.hardware.network_analyzer.NetworkAnalyzer._get_performance_metrics', return_value={})
    def test_get_network_info_caching(self, mock_perf, mock_driver, mock_wireless, mock_detailed, analyzer, mock_si):
        """Test that the main get_network_info method caches results."""
        mock_si.run_command.return_value = CommandResult(success=True, stdout="data", stderr="", returncode=0)
        analyzer.get_network_info()
        analyzer.get_network_info()
        # The underlying _get_basic_network_info method should be called only once.
        # We check the number of calls to run_command made by it.
        assert mock_si.run_command.call_count == 2

    def test_parse_ip_addr_output(self, analyzer):
        """Test parsing of 'ip addr' output."""
        parsed = analyzer._parse_ip_addr_output(MOCK_IP_ADDR_OUTPUT)
        assert len(parsed) == 2
        # Order might not be guaranteed, so check for existence
        lo_if = next((iface for iface in parsed if iface['name'] == 'lo'), None)
        eth_if = next((iface for iface in parsed if iface['name'] == 'eth0'), None)
        assert lo_if is not None
        assert eth_if is not None

        assert lo_if['state'] == 'UNKNOWN'
        assert lo_if['mac'] == '00:00:00:00:00:00'
        assert len(lo_if['addresses']) == 2

        assert eth_if['state'] == 'UP'
        assert eth_if['mac'] == '0c:de:ad:be:ef:00'
        assert eth_if['addresses'][0]['address'] == '192.168.1.10/24'
        assert eth_if['addresses'][1]['address'] == 'fe80::dead:beef:feef:0/64'

    def test_parse_ip_link_output(self, analyzer):
        """Test parsing of 'ip -s link' output."""
        parsed = analyzer._parse_ip_link_output(MOCK_IP_LINK_OUTPUT)
        stats = parsed['interface_statistics']
        assert 'lo' in stats
        assert 'eth0' in stats
        assert stats['lo']['rx']['bytes'] == 12345
        assert stats['eth0']['tx']['packets'] == 2000
        assert stats['eth0']['rx']['errors'] == 5
        assert stats['eth0']['tx']['dropped'] == 2

    def test_parse_iwconfig_output(self, analyzer):
        """Test parsing of 'iwconfig' output."""
        parsed = analyzer._parse_iwconfig_output(MOCK_IWCONFIG_OUTPUT)
        assert len(parsed) == 1
        wlan0 = parsed[0]
        assert wlan0['name'] == 'wlan0'
        assert wlan0['essid'] == 'MyWiFi'
        assert wlan0['mode'] == 'Managed'
        assert wlan0['frequency'] == '5.24 GHz'
        assert wlan0['access_point'] == '01:02:03:04:05:06'
        assert wlan0['bit_rate'] == '866.7 Mb/s'
        assert wlan0['signal_level'] == '-40 dBm'

    def test_parse_ethtool_output(self, analyzer):
        """Test parsing of 'ethtool -S' output."""
        parsed = analyzer._parse_ethtool_output(MOCK_ETHTOOL_OUTPUT)
        assert parsed['rx_packets'] == 1000
        assert parsed['tx_bytes'] == 2000000

    def test_get_driver_details(self, analyzer, mock_si):
        """Test parsing of 'modinfo' output."""
        mock_si.run_command.return_value = CommandResult(True, MOCK_MODINFO_OUTPUT, "", 0)
        details = analyzer._get_driver_details("e1000e")
        assert details['version'] == '3.2.6-k'
        assert details['license'] == 'GPL'
        assert details['description'] == 'Intel(R) PRO/1000 Network Driver'

    def test_get_interface_details(self, analyzer, mock_si):
        """Test gathering of interface details from /sys."""
        def read_file_side_effect(path):
            return {
                '/sys/class/net/eth0/type': '1',
                '/sys/class/net/eth0/speed': '1000',
                '/sys/class/net/eth0/duplex': 'full',
                '/sys/class/net/eth0/address': 'aa:bb:cc:dd:ee:ff',
                '/sys/class/net/eth0/flags': '0x1003',  # UP, BROADCAST, RUNNING
                '/sys/class/net/eth0/statistics/rx_bytes': '1234',
                '/sys/class/net/eth0/statistics/tx_bytes': '5678',
            }.get(path)

        mock_si.read_file.side_effect = read_file_side_effect
        mock_si.run_command.return_value = CommandResult(True, "rx_bytes\ntx_bytes", "", 0)

        details = analyzer._get_interface_details("eth0")
        assert details['name'] == 'eth0'
        assert details['type'] == 'ethernet'
        assert details['speed'] == 1000
        assert details['duplex'] == 'full'
        assert details['address'] == 'aa:bb:cc:dd:ee:ff'
        assert 'UP' in details['decoded_flags']
        assert 'BROADCAST' in details['decoded_flags']
        assert 'statistics' in details
        assert details['statistics']['rx_bytes'] == 1234

    def test_full_run_with_failures(self, analyzer, mock_si):
        """Test a full run where some commands fail."""
        with patch.object(analyzer, 'logger') as mock_logger:
            def command_side_effect(cmd):
                if cmd == ['ip', '-s', 'addr']:
                    return CommandResult(True, MOCK_IP_ADDR_OUTPUT, "", 0)
                if cmd == ['ls', '/sys/class/net/']:
                    return CommandResult(True, "lo eth0", "", 0)
                if cmd == ['ethtool', '-i', 'eth0']:
                    return CommandResult(True, "driver: e1000e", "", 0)
                # Fail other commands
                return CommandResult(False, "", "command not found", 1)

            mock_si.run_command.side_effect = command_side_effect
            mock_si.read_file.return_value = "1"  # for type

            info = analyzer.get_network_info()

            assert 'interfaces' in info
            assert 'wireless_interfaces' not in info  # iwconfig failed
            assert 'ethtool_statistics' not in info  # ethtool -S failed
            assert 'driver_info' in info
            assert info['driver_info'][0]['driver'] == 'e1000e'
            assert 'ip_link_error' in info  # ip -s link failed
            assert mock_logger.info.called