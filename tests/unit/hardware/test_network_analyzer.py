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

import unittest
from unittest.mock import MagicMock, patch

import psutil
from tinel.hardware.network_analyzer import NetworkAnalyzer
from tinel.interfaces import CommandResult


class TestNetworkAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = NetworkAnalyzer(self.mock_system_interface)

    def test_get_network_info_caching(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        with patch('psutil.net_if_addrs', return_value={}), \
             patch('psutil.net_if_stats', return_value={}), \
             patch('psutil.net_io_counters', return_value={}):
            self.analyzer.get_network_info()
            call_count = self.mock_system_interface.run_command.call_count
            self.analyzer.get_network_info()
            self.assertEqual(self.mock_system_interface.run_command.call_count, call_count)

    def test_get_basic_network_info(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000", stderr="", returncode=0)
        interfaces = self.analyzer._get_basic_network_info()
        self.assertEqual(len(interfaces), 1)

    def test_parse_ip_addr_output(self):
        output = "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000\n    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\n    inet 127.0.0.1/8 scope host lo\n       valid_lft forever preferred_lft forever\n    inet6 ::1/128 scope host \n       valid_lft forever preferred_lft forever"
        interfaces = self.analyzer._parse_ip_addr_output(output)
        self.assertEqual(len(interfaces), 1)
        self.assertEqual(interfaces[0].name, "lo")

    def test_parse_ip_addr_output_no_details(self):
        output = "1: lo:"
        interfaces = self.analyzer._parse_ip_addr_output(output)
        self.assertEqual(len(interfaces), 1)

    def test_parse_ip_link_output(self):
        output = "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000\n    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\n    RX: bytes  packets  errors  dropped overrun mcast\n    624        8        0       0       0       0\n    TX: bytes  packets  errors  dropped carrier collsns\n    624        8        0       0       0       0"
        stats = self.analyzer._parse_ip_link_output(output)
        self.assertIn("lo", stats)

    def test_parse_iwconfig_output(self):
        output = "wlan0     IEEE 802.11  ESSID:\"MyNetwork\"  \n          Mode:Managed  Frequency:2.412 GHz  Access Point: 00:11:22:33:44:55   \n          Bit Rate=72.2 Mb/s   Tx-Power=20 dBm   \n          Retry short limit:7   RTS thr:off   Fragment thr:off\n          Power Management:on\n          Link Quality=70/70  Signal level=-40 dBm  \n          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0\n          Tx excessive retries:0  Invalid misc:0   Missed beacon:0"
        interfaces = self.analyzer._parse_iwconfig_output(output)
        self.assertEqual(len(interfaces), 1)

    def test_parse_ethtool_output(self):
        output = "     rx_bytes: 1234\n     tx_bytes: 5678"
        stats = self.analyzer._parse_ethtool_output(output)
        self.assertEqual(stats["rx_bytes"], 1234)

    def test_get_driver_details(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="filename: /lib/modules/5.4.0-77-generic/kernel/drivers/net/ethernet/intel/e1000e/e1000e.ko", stderr="", returncode=0)
        details = self.analyzer._get_driver_details("e1000e")
        self.assertIn("filename", details)

    def test_get_interface_details(self):
        self.mock_system_interface.read_file.side_effect = ["1", "eth0", "00:11:22:33:44:55", "1500", "up", "1000", "full", "0x1003"]
        self.mock_system_interface.readlink.return_value = "../../../devices/pci0000:00/0000:00:1f.6"
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="rx_bytes\ntx_bytes", stderr="", returncode=0)
        interface = self.analyzer._get_interface_details("eth0")
        self.assertEqual(interface.name, "eth0")

    def test_full_run_with_failures(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="failed", returncode=1)
        with patch('psutil.net_if_addrs', side_effect=Exception("psutil failed")), \
             patch('psutil.net_if_stats', side_effect=Exception("psutil failed")), \
             patch('psutil.net_io_counters', side_effect=Exception("psutil failed")):
            info = self.analyzer.get_network_info()
            self.assertEqual(len(info.interfaces), 0)

    def test_get_detailed_network_info_ls_fails(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="ls failed", returncode=1)
        self.assertEqual(self.analyzer._get_detailed_network_info(), [])

    def test_parse_ip_addr_empty_output(self):
        self.assertEqual(self.analyzer._parse_ip_addr_output(""), [])

    def test_parse_ip_link_malformed_output(self):
        self.assertEqual(self.analyzer._parse_ip_link_output("malformed"), {})

    def test_get_wireless_info_no_tools(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        self.assertEqual(self.analyzer._get_wireless_info(), [])

    def test_get_performance_metrics_no_tools(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        with patch('psutil.net_io_counters', return_value={}):
            metrics = self.analyzer._get_performance_metrics()
            self.assertEqual(metrics.netstat_statistics, [])

    def test_ip_addr_failure(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        with patch('psutil.net_if_addrs', return_value={}), \
             patch('psutil.net_if_stats', return_value={}):
            self.assertEqual(self.analyzer._get_basic_network_info(), [])

    def test_successful_iwconfig(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="wlan0     IEEE 802.11", stderr="", returncode=0)
        self.assertNotEqual(self.analyzer._get_wireless_info(), [])

    def test_successful_iw_list(self):
        self.assertEqual(self.analyzer._parse_iw_list_output("some output"), {"raw": "some output"})

    def test_successful_netstat(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="Kernel Interface table\nIface      MTU    RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg\neth0      1500   1234      0      0      0     5678      0      0      0 BMRU", stderr="", returncode=0)
        with patch.object(self.analyzer, '_get_psutil_io_counters', return_value={}):
            metrics = self.analyzer._get_performance_metrics()
            self.assertNotEqual(metrics.netstat_statistics, [])

    def test_successful_ethtool_stats(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="", returncode=1), # netstat
            CommandResult(success=True, stdout="eth0", stderr="", returncode=0), # ls
            CommandResult(success=True, stdout="rx_bytes: 100", stderr="", returncode=0) # ethtool
        ]
        with patch.object(self.analyzer, '_get_psutil_io_counters', return_value={}):
            metrics = self.analyzer._get_performance_metrics()
            self.assertIn("eth0", metrics.ethtool_statistics)

    def test_driver_with_details(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="eth0", stderr="", returncode=0), # ls
            CommandResult(success=True, stdout="driver: e1000e", stderr="", returncode=0), # ethtool
            CommandResult(success=True, stdout="version: 3.2.6-k", stderr="", returncode=0) # modinfo
        ]
        info = self.analyzer._get_driver_info()
        self.assertEqual(info[0].driver, "e1000e")

    def test_ethtool_no_driver_match(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="no driver here", stderr="", returncode=0)
        self.assertIsNone(self.analyzer._get_interface_driver("eth0"))

    def test_parse_iwconfig_with_empty_blocks(self):
        self.assertEqual(self.analyzer._parse_iwconfig_output("\n\n"), [])

    def test_parse_iwconfig_no_interface_name(self):
        self.assertEqual(self.analyzer._parse_iwconfig_output("  no name"), [])

    def test_parse_iwconfig_no_wireless_extensions(self):
        self.assertEqual(self.analyzer._parse_iwconfig_output("eth0      no wireless extensions."), [])

    def test_parse_netstat_short_output(self):
        self.assertEqual(self.analyzer._parse_netstat_output("Header\n"), [])

    def test_parse_netstat_valid_output(self):
        output = "Kernel Interface table\nIface      MTU    RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg\neth0      1500   1234      0      0      0     5678      0      0      0 BMRU"
        self.assertNotEqual(self.analyzer._parse_netstat_output(output), [])

    def test_parse_iwconfig_partial_fields(self):
        self.assertEqual(len(self.analyzer._parse_iwconfig_output("wlan0     ESSID:\"test\"")), 1)

    def test_parse_iwconfig_truly_empty_block(self):
        self.assertEqual(self.analyzer._parse_iwconfig_output("wlan0\n\neth0"), 1)

    def test_parse_iwconfig_all_fields_missing(self):
        self.assertEqual(len(self.analyzer._parse_iwconfig_output("wlan0")), 1)

    def test_parse_ip_addr_no_state_match(self):
        interfaces = self.analyzer._parse_ip_addr_output("1: lo: <>")
        self.assertIsNone(interfaces[0].state)

    def test_parse_ip_addr_no_mac_match(self):
        interfaces = self.analyzer._parse_ip_addr_output("1: lo:\n    no mac")
        self.assertIsNone(interfaces[0].mac)

    def test_parse_ip_addr_no_ip_match(self):
        interfaces = self.analyzer._parse_ip_addr_output("1: lo:\n    no ip")
        self.assertEqual(interfaces[0].addresses, [])

    def test_get_interface_details_no_type(self):
        self.mock_system_interface.read_file.return_value = None
        self.assertIsNone(self.analyzer._get_interface_details("eth0"))

    def test_get_interface_details_no_flags(self):
        self.mock_system_interface.read_file.side_effect = ["1", None] # type, then no flags
        self.assertIsNotNone(self.analyzer._get_interface_details("eth0"))

    def test_get_interface_details_no_statistics(self):
        self.mock_system_interface.read_file.side_effect = ["1", "0x1003"]
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        self.assertIsNotNone(self.analyzer._get_interface_details("eth0"))

    def test_get_detailed_network_info_no_interfaces(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)
        self.assertEqual(self.analyzer._get_detailed_network_info(), [])

    def test_get_driver_info_no_drivers(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="eth0", stderr="", returncode=0)
        with patch.object(self.analyzer, '_get_interface_driver', return_value=None):
            self.assertEqual(self.analyzer._get_driver_info(), [])

    def test_get_performance_metrics_no_ethtool_stats(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="Kernel Interface table\nIface MTU\neth0 1500", stderr="", returncode=0), # netstat
            CommandResult(success=True, stdout="eth0", stderr="", returncode=0), # ls
            CommandResult(success=False, stdout="", stderr="", returncode=1) # ethtool
        ]
        metrics = self.analyzer._get_performance_metrics()
        self.assertEqual(metrics.ethtool_statistics, {})

    def test_parse_ip_link_no_interface_match(self):
        self.assertEqual(self.analyzer._parse_ip_link_output("no match"), {})

    def test_parse_ip_link_incomplete_rx_values(self):
        output = "1: lo:\n    RX: bytes packets errors\n    1 2 3"
        stats = self.analyzer._parse_ip_link_output(output)
        self.assertNotIn("rx", stats["lo"])

    def test_parse_ip_link_incomplete_tx_values(self):
        output = "1: lo:\n    TX: bytes packets errors\n    1 2 3"
        stats = self.analyzer._parse_ip_link_output(output)
        self.assertNotIn("tx", stats["lo"])

    def test_parse_ethtool_output_no_colon(self):
        self.assertEqual(self.analyzer._parse_ethtool_output("no colon"), {})

    def test_parse_ethtool_output_non_numeric(self):
        self.assertEqual(self.analyzer._parse_ethtool_output("key: value"), {})

    def test_get_wireless_info_iwconfig_empty_stdout(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)
        self.assertEqual(self.analyzer._get_wireless_info(), [])

    def test_parse_ip_addr_no_interface_match(self):
        self.assertEqual(self.analyzer._parse_ip_addr_output("no match"), [])

    def test_parse_netstat_insufficient_values(self):
        self.assertEqual(self.analyzer._parse_netstat_output("Header1 Header2\nVal1"), [])

    def test_get_detailed_network_info_with_loopback_and_interface(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="lo eth0", stderr="", returncode=0)
        with patch.object(self.analyzer, '_get_interface_details', return_value=MagicMock()):
            self.assertEqual(len(self.analyzer._get_detailed_network_info()), 1)

    def test_get_wireless_info_iwconfig_success_iw_success(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="wlan0", stderr="", returncode=0)
        self.assertNotEqual(self.analyzer._get_wireless_info(), [])

    def test_get_driver_info_multiple_interfaces(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="eth0 eth1", stderr="", returncode=0)
        with patch.object(self.analyzer, '_get_interface_driver', return_value="e1000e"), \
             patch.object(self.analyzer, '_get_driver_details', return_value={}):
            self.assertEqual(len(self.analyzer._get_driver_info()), 2)

    def test_get_performance_metrics_mixed_ethtool(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="Iface\neth0\neth1", stderr="", returncode=0), # netstat
            CommandResult(success=True, stdout="eth0 eth1", stderr="", returncode=0), # ls
            CommandResult(success=True, stdout="rx: 1", stderr="", returncode=0), # ethtool eth0
            CommandResult(success=False, stdout="", stderr="", returncode=1), # ethtool eth1
        ]
        metrics = self.analyzer._get_performance_metrics()
        self.assertIn("eth0", metrics.ethtool_statistics)
        self.assertNotIn("eth1", metrics.ethtool_statistics)

    def test_get_driver_details_empty_modinfo(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)
        self.assertEqual(self.analyzer._get_driver_details("e1000e"), {})

    def test_get_detailed_network_info_skip_first_continue_second(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="eth0 eth1", stderr="", returncode=0)
        def get_details_mock(iface):
            if iface == "eth0": return None
            return MagicMock()
        with patch.object(self.analyzer, '_get_interface_details', side_effect=get_details_mock):
            self.assertEqual(len(self.analyzer._get_detailed_network_info()), 1)

    def test_get_driver_info_skip_then_add(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="eth0 eth1", stderr="", returncode=0)
        def get_driver_mock(iface):
            if iface == "eth0": return None
            return "e1000e"
        with patch.object(self.analyzer, '_get_interface_driver', side_effect=get_driver_mock), \
             patch.object(self.analyzer, '_get_driver_details', return_value={}):
            self.assertEqual(len(self.analyzer._get_driver_info()), 1)

    def test_get_performance_metrics_skip_then_add_ethtool(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="Iface\neth0\neth1", stderr="", returncode=0), # netstat
            CommandResult(success=True, stdout="eth0 eth1", stderr="", returncode=0), # ls
            CommandResult(success=False, stdout="", stderr="", returncode=1), # ethtool eth0
            CommandResult(success=True, stdout="rx: 1", stderr="", returncode=0), # ethtool eth1
        ]
        metrics = self.analyzer._get_performance_metrics()
        self.assertIn("eth1", metrics.ethtool_statistics)

    def test_get_wireless_info_iwconfig_success_then_iw_fail(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="wlan0", stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="", returncode=1)
        ]
        self.assertNotEqual(self.analyzer._get_wireless_info(), [])

    def test_get_basic_network_info_ip_addr_fail_no_stderr(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        with patch('psutil.net_if_addrs', return_value={}), \
             patch('psutil.net_if_stats', return_value={}):
            self.analyzer._get_basic_network_info()
            self.analyzer.logger.warning.assert_any_call("Failed to run 'ip addr', falling back to psutil: %s", "")

    def test_get_detailed_network_info_empty_interface_info(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="eth0", stderr="", returncode=0)
        with patch.object(self.analyzer, '_get_interface_details', return_value=None):
            self.assertEqual(self.analyzer._get_detailed_network_info(), [])

    def test_get_driver_info_no_driver_details(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="eth0", stderr="", returncode=0)
        with patch.object(self.analyzer, '_get_interface_driver', return_value="e1000e"), \
             patch.object(self.analyzer, '_get_driver_details', return_value={}):
            self.assertEqual(self.analyzer._get_driver_info()[0].driver_details, {})

    def test_parse_ip_addr_output_no_current_interface(self):
        self.assertEqual(self.analyzer._parse_ip_addr_output("  inet 127.0.0.1/8"), [])

    def test_get_interface_details_unknown_type(self):
        self.mock_system_interface.read_file.return_value = "999"
        iface = self.analyzer._get_interface_details("eth0")
        self.assertEqual(iface.type, "unknown (999)")

    def test_get_driver_info_no_driver(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="eth0", stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="", returncode=1)
        ]
        self.assertEqual(self.analyzer._get_driver_info(), [])

    def test_get_interface_details_no_stats(self):
        self.mock_system_interface.read_file.side_effect = ["1"]
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        iface = self.analyzer._get_interface_details("eth0")
        self.assertIsNone(iface.statistics)

    def test_parse_ip_addr_output_no_state(self):
        iface = self.analyzer._parse_ip_addr_output("1: lo: <>")[0]
        self.assertIsNone(iface.state)

    def test_get_basic_network_info_ip_link_fail_no_stderr(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="1: lo:", stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="", returncode=1)
        ]
        self.analyzer._get_basic_network_info()
        self.analyzer.logger.warning.assert_called_with("Failed to run 'ip -s link', skipping statistics: %s", "")

    def test_get_detailed_network_info_interface_info_is_false(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="eth0", stderr="", returncode=0)
        with patch.object(self.analyzer, '_get_interface_details', return_value=None):
            self.assertEqual(self.analyzer._get_detailed_network_info(), [])

    def test_get_driver_info_driver_found_no_details(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="eth0", stderr="", returncode=0),
            CommandResult(success=True, stdout="driver: e1000e", stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="", returncode=1)
        ]
        self.assertEqual(self.analyzer._get_driver_info()[0].driver_details, {})

    def test_parse_ip_addr_output_continues_after_no_match(self):
        output = "line without match\n1: lo:"
        self.assertEqual(len(self.analyzer._parse_ip_addr_output(output)), 1)

    def test_get_performance_metrics_ls_fails(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        with patch('psutil.net_io_counters', return_value={}):
            metrics = self.analyzer._get_performance_metrics()
            self.assertEqual(metrics.ethtool_statistics, {})

    def test_get_driver_info_ls_fails(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        self.assertEqual(self.analyzer._get_driver_info(), [])

    def test_get_driver_info_ls_empty(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)
        self.assertEqual(self.analyzer._get_driver_info(), [])

    def test_get_driver_info_only_lo(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="lo", stderr="", returncode=0)
        self.assertEqual(self.analyzer._get_driver_info(), [])

    def test_parse_ip_addr_malformed_interface_line(self):
        self.assertEqual(self.analyzer._parse_ip_addr_output("1: malformed"), [])

if __name__ == "__main__":
    unittest.main()