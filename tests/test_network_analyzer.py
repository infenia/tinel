#!/usr/bin/env python3
"""Tests for the Network Analyzer module.

Copyright 2024 Infenia Private Limited

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

from infenix.hardware.network_analyzer import NetworkAnalyzer
from infenix.interfaces import CommandResult


class TestNetworkAnalyzer(unittest.TestCase):
    """Test cases for the NetworkAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.analyzer = NetworkAnalyzer(self.mock_system)
    
    def test_get_network_info(self):
        """Test getting comprehensive network hardware information."""
        # Mock system interface responses
        self._setup_basic_mocks()
        
        # Call the method under test
        result = self.analyzer.get_network_info()
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('interfaces', result)
        self.assertGreater(len(result['interfaces']), 0)
    
    def test_parse_ip_addr_output(self):
        """Test parsing ip addr output."""
        ip_addr_output = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.100/24 brd 192.168.1.255 scope global dynamic noprefixroute eth0
       valid_lft 86390sec preferred_lft 86390sec
    inet6 fe80::1234:5678:9abc:def0/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever"""
        
        result = self.analyzer._parse_ip_addr_output(ip_addr_output)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'lo')
        self.assertEqual(result[0]['state'], 'UNKNOWN')
        self.assertEqual(result[0]['mac'], '00:00:00:00:00:00')
        self.assertEqual(len(result[0]['addresses']), 2)
        self.assertEqual(result[0]['addresses'][0]['family'], 'inet')
        self.assertEqual(result[0]['addresses'][0]['address'], '127.0.0.1/8')
        
        self.assertEqual(result[1]['name'], 'eth0')
        self.assertEqual(result[1]['state'], 'UP')
        self.assertEqual(result[1]['mac'], '00:11:22:33:44:55')
        self.assertEqual(len(result[1]['addresses']), 2)
        self.assertEqual(result[1]['addresses'][0]['family'], 'inet')
        self.assertEqual(result[1]['addresses'][0]['address'], '192.168.1.100/24')
    
    def test_parse_iwconfig_output(self):
        """Test parsing iwconfig output."""
        iwconfig_output = """lo        no wireless extensions.

eth0      no wireless extensions.

wlan0     IEEE 802.11  ESSID:"MyWiFi"  
          Mode:Managed  Frequency:2.412 GHz  Access Point: 00:11:22:33:44:55   
          Bit Rate=54 Mb/s   Tx-Power=15 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=70/70  Signal level=-30 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:0   Missed beacon:0"""
        
        result = self.analyzer._parse_iwconfig_output(iwconfig_output)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'wlan0')
        self.assertEqual(result[0]['essid'], 'MyWiFi')
        self.assertEqual(result[0]['mode'], 'Managed')
        self.assertEqual(result[0]['frequency'], 2.412)
        self.assertEqual(result[0]['access_point'], '00:11:22:33:44:55')
        self.assertEqual(result[0]['bit_rate'], '54 Mb/s')
        self.assertEqual(result[0]['signal_level'], -30)
    
    def test_get_interface_details(self):
        """Test getting detailed information for a specific network interface."""
        # Mock system interface responses
        self.mock_system.read_file.side_effect = lambda path: {
            '/sys/class/net/eth0/type': '1',
            '/sys/class/net/eth0/speed': '1000',
            '/sys/class/net/eth0/duplex': 'full',
            '/sys/class/net/eth0/mtu': '1500',
            '/sys/class/net/eth0/carrier': '1',
            '/sys/class/net/eth0/operstate': 'up',
            '/sys/class/net/eth0/address': '00:11:22:33:44:55',
            '/sys/class/net/eth0/flags': '0x1003',
            '/sys/class/net/eth0/statistics/rx_bytes': '1234567',
            '/sys/class/net/eth0/statistics/tx_bytes': '7654321',
        }.get(path, None)
        
        self.mock_system.file_exists.return_value = True
        
        self.mock_system.run_command.side_effect = lambda cmd: {
            'ls /sys/class/net/eth0/statistics': 
                CommandResult(True, 'rx_bytes\ntx_bytes\nrx_packets\ntx_packets', '', 0),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))
        
        result = self.analyzer._get_interface_details('eth0')
        
        self.assertEqual(result['name'], 'eth0')
        self.assertEqual(result['type'], 'ethernet')
        self.assertEqual(result['speed'], '1000 Mbps')
        self.assertEqual(result['duplex'], 'full')
        self.assertEqual(result['mtu'], 1500)
        self.assertEqual(result['carrier'], True)
        self.assertEqual(result['operstate'], 'up')
        self.assertEqual(result['mac'], '00:11:22:33:44:55')
        self.assertEqual(result['flags'], 0x1003)
        self.assertIn('statistics', result)
        self.assertEqual(result['statistics']['rx_bytes'], 1234567)
        self.assertEqual(result['statistics']['tx_bytes'], 7654321)
    
    def _setup_basic_mocks(self):
        """Set up basic mocks for system interface."""
        # Mock ip addr output
        ip_addr_output = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.100/24 brd 192.168.1.255 scope global dynamic noprefixroute eth0
       valid_lft 86390sec preferred_lft 86390sec
    inet6 fe80::1234:5678:9abc:def0/64 scope link noprefixroute 
       valid_lft forever preferred_lft forever"""
        
        # Mock ip -s link output
        ip_link_output = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    RX: bytes  packets  errors  dropped overrun mcast   
    1234       12       0       0       0       0       
    TX: bytes  packets  errors  dropped carrier collsns 
    1234       12       0       0       0       0       
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped overrun mcast   
    1234567    1234     0       0       0       0       
    TX: bytes  packets  errors  dropped carrier collsns 
    7654321    4321     0       0       0       0"""
        
        # Mock iwconfig output
        iwconfig_output = """lo        no wireless extensions.

eth0      no wireless extensions.

wlan0     IEEE 802.11  ESSID:"MyWiFi"  
          Mode:Managed  Frequency:2.412 GHz  Access Point: 00:11:22:33:44:55   
          Bit Rate=54 Mb/s   Tx-Power=15 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=70/70  Signal level=-30 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:0   Missed beacon:0"""
        
        # Mock ls /sys/class/net/ output
        ls_net_output = "eth0\nlo\nwlan0"
        
        # Set up mock responses
        self.mock_system.run_command.side_effect = lambda cmd: {
            'ip -s addr': 
                CommandResult(True, ip_addr_output, '', 0),
            'ip -s link': 
                CommandResult(True, ip_link_output, '', 0),
            'iwconfig': 
                CommandResult(True, iwconfig_output, '', 0),
            'ls /sys/class/net/': 
                CommandResult(True, ls_net_output, '', 0),
            'netstat -i': 
                CommandResult(True, 'Iface   MTU Met   RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg\neth0   1500 0     1234      0      0 0          4321      0      0      0 BMRU', '', 0),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))
        
        # Mock file_exists
        self.mock_system.file_exists.return_value = True
        
        # Mock read_file
        self.mock_system.read_file.side_effect = lambda path: {
            '/sys/class/net/eth0/type': '1',
            '/sys/class/net/eth0/speed': '1000',
            '/sys/class/net/eth0/duplex': 'full',
            '/sys/class/net/eth0/mtu': '1500',
            '/sys/class/net/eth0/carrier': '1',
            '/sys/class/net/eth0/operstate': 'up',
            '/sys/class/net/eth0/address': '00:11:22:33:44:55',
            '/sys/class/net/eth0/flags': '0x1003',
        }.get(path, None)


if __name__ == '__main__':
    unittest.main()