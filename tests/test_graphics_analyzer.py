#!/usr/bin/env python3
"""Tests for the Graphics Analyzer module.

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

from infenix.hardware.graphics_analyzer import GraphicsAnalyzer
from infenix.interfaces import CommandResult


class TestGraphicsAnalyzer(unittest.TestCase):
    """Test cases for the GraphicsAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.analyzer = GraphicsAnalyzer(self.mock_system)
    
    def test_get_graphics_info(self):
        """Test getting comprehensive graphics hardware information."""
        # Mock system interface responses
        self._setup_basic_mocks()
        
        # Call the method under test
        result = self.analyzer.get_graphics_info()
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('gpus', result)
        self.assertGreater(len(result['gpus']), 0)
    
    def test_parse_lspci_vga_output(self):
        """Test parsing lspci output for VGA devices."""
        lspci_output = """00:02.0 VGA compatible controller [0300]: Intel Corporation UHD Graphics 620 [8086:5917] (rev 07) (prog-if 00 [VGA controller])
	Subsystem: Dell Device [1028:087c]
	Flags: bus master, fast devsel, latency 0, IRQ 127
	Memory at eb000000 (64-bit, non-prefetchable) [size=16M]
	Memory at 80000000 (64-bit, prefetchable) [size=256M]
	I/O ports at f000 [size=64]
	Expansion ROM at 000c0000 [virtual] [disabled] [size=128K]
	Capabilities: <access denied>
	Kernel driver in use: i915
	Kernel modules: i915

01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GP107M [GeForce GTX 1050 Mobile] [10de:1c8d] (rev a1) (prog-if 00 [VGA controller])
	Subsystem: Dell Device [1028:087c]
	Flags: bus master, fast devsel, latency 0, IRQ 128
	Memory at ec000000 (32-bit, non-prefetchable) [size=16M]
	Memory at c0000000 (64-bit, prefetchable) [size=256M]
	Memory at d0000000 (64-bit, prefetchable) [size=32M]
	I/O ports at e000 [size=128]
	Expansion ROM at ed000000 [disabled] [size=512K]
	Capabilities: <access denied>
	Kernel driver in use: nvidia
	Kernel modules: nvidiafb, nouveau, nvidia_drm, nvidia"""
        
        result = self.analyzer._parse_lspci_vga_output(lspci_output)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['address'], '00:02.0')
        self.assertEqual(result[0]['description'], 'VGA compatible controller [0300]: Intel Corporation UHD Graphics 620')
        self.assertEqual(result[0]['vendor_id'], '8086')
        self.assertEqual(result[0]['device_id'], '5917')
        self.assertEqual(result[0]['vendor'], 'Intel')
        self.assertEqual(result[0]['driver'], 'i915')
        
        self.assertEqual(result[1]['address'], '01:00.0')
        self.assertEqual(result[1]['description'], 'VGA compatible controller [0300]: NVIDIA Corporation GP107M [GeForce GTX 1050 Mobile]')
        self.assertEqual(result[1]['vendor_id'], '10de')
        self.assertEqual(result[1]['device_id'], '1c8d')
        self.assertEqual(result[1]['vendor'], 'NVIDIA')
        self.assertEqual(result[1]['driver'], 'nvidia')
    
    def test_parse_xrandr_output(self):
        """Test parsing xrandr output."""
        xrandr_output = """Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 8192 x 8192
eDP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 344mm x 194mm
   1920x1080     60.01*+  59.97    59.96    59.93    48.00  
   1680x1050     59.95    59.88  
   1600x1024     60.17  
   1400x1050     59.98  
   1600x900      59.99    59.94    59.95    59.82  
   1280x1024     60.02  
   1440x900      59.89  
   1400x900      59.96    59.88  
   1280x960      60.00  
   1440x810      60.00    59.97  
   1368x768      59.88    59.85  
   1360x768      59.80    59.96  
   1280x800      59.99    59.97    59.81    59.91  
   1152x864      60.00  
   1280x720      60.00    59.99    59.86    59.74  
   1024x768      60.04    60.00  
   960x720       60.00  
   928x696       60.05  
   896x672       60.01  
   1024x576      59.95    59.96    59.90    59.82  
   960x600       59.93    60.00  
   960x540       59.96    59.99    59.63    59.82  
   800x600       60.00    60.32    56.25  
   840x525       60.01    59.88  
   864x486       59.92    59.57  
   800x512       60.17  
   700x525       59.98  
   800x450       59.95    59.82  
   640x512       60.02  
   720x450       59.89  
   700x450       59.96    59.88  
   640x480       60.00    59.94  
   720x405       59.51    58.99  
   684x384       59.88    59.85  
   680x384       59.80    59.96  
   640x400       59.88    59.98  
   576x432       60.06  
   640x360       59.86    59.83    59.84    59.32  
   512x384       60.00  
   512x288       60.00    59.92  
   480x270       59.63    59.82  
   400x300       60.32    56.34  
   432x243       59.92    59.57  
   320x240       60.05  
   360x202       59.51    59.13  
   320x180       59.84    59.32  
HDMI-1 disconnected (normal left inverted right x axis y axis)
DP-1 disconnected (normal left inverted right x axis y axis)
HDMI-2 disconnected (normal left inverted right x axis y axis)"""
        
        result = self.analyzer._parse_xrandr_output(xrandr_output)
        
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['name'], 'eDP-1')
        self.assertEqual(result[0]['status'], 'connected')
        self.assertEqual(result[0]['primary'], True)
        self.assertEqual(result[0]['width'], 1920)
        self.assertEqual(result[0]['height'], 1080)
        self.assertEqual(result[0]['x'], 0)
        self.assertEqual(result[0]['y'], 0)
        
        self.assertEqual(result[1]['name'], 'HDMI-1')
        self.assertEqual(result[1]['status'], 'disconnected')
        
        self.assertEqual(result[2]['name'], 'DP-1')
        self.assertEqual(result[2]['status'], 'disconnected')
        
        self.assertEqual(result[3]['name'], 'HDMI-2')
        self.assertEqual(result[3]['status'], 'disconnected')
    
    def _setup_basic_mocks(self):
        """Set up basic mocks for system interface."""
        # Mock lspci output
        lspci_output = """00:02.0 VGA compatible controller [0300]: Intel Corporation UHD Graphics 620 [8086:5917] (rev 07) (prog-if 00 [VGA controller])
	Subsystem: Dell Device [1028:087c]
	Flags: bus master, fast devsel, latency 0, IRQ 127
	Memory at eb000000 (64-bit, non-prefetchable) [size=16M]
	Memory at 80000000 (64-bit, prefetchable) [size=256M]
	I/O ports at f000 [size=64]
	Expansion ROM at 000c0000 [virtual] [disabled] [size=128K]
	Capabilities: <access denied>
	Kernel driver in use: i915
	Kernel modules: i915"""
        
        # Mock xrandr output
        xrandr_output = """Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 8192 x 8192
eDP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 344mm x 194mm
   1920x1080     60.01*+  59.97    59.96    59.93    48.00  
   1680x1050     59.95    59.88  
   1600x1024     60.17  
   1400x1050     59.98  
   1600x900      59.99    59.94    59.95    59.82  
   1280x1024     60.02  
   1440x900      59.89  
   1400x900      59.96    59.88  
   1280x960      60.00  
   1440x810      60.00    59.97  
   1368x768      59.88    59.85  
   1360x768      59.80    59.96  
   1280x800      59.99    59.97    59.81    59.91  
   1152x864      60.00  
   1280x720      60.00    59.99    59.86    59.74  
   1024x768      60.04    60.00  
   960x720       60.00  
   928x696       60.05  
   896x672       60.01  
   1024x576      59.95    59.96    59.90    59.82  
   960x600       59.93    60.00  
   960x540       59.96    59.99    59.63    59.82  
   800x600       60.00    60.32    56.25  
   840x525       60.01    59.88  
   864x486       59.92    59.57  
   800x512       60.17  
   700x525       59.98  
   800x450       59.95    59.82  
   640x512       60.02  
   720x450       59.89  
   700x450       59.96    59.88  
   640x480       60.00    59.94  
   720x405       59.51    58.99  
   684x384       59.88    59.85  
   680x384       59.80    59.96  
   640x400       59.88    59.98  
   576x432       60.06  
   640x360       59.86    59.83    59.84    59.32  
   512x384       60.00  
   512x288       60.00    59.92  
   480x270       59.63    59.82  
   400x300       60.32    56.34  
   432x243       59.92    59.57  
   320x240       60.05  
   360x202       59.51    59.13  
   320x180       59.84    59.32  
HDMI-1 disconnected (normal left inverted right x axis y axis)
DP-1 disconnected (normal left inverted right x axis y axis)
HDMI-2 disconnected (normal left inverted right x axis y axis)"""
        
        # Mock lsmod output
        lsmod_output = """Module                  Size  Used by
i915                 2859008  3
intel_gtt              24576  1 i915
drm_kms_helper        184320  1 i915
drm                   491520  4 drm_kms_helper,i915
i2c_algo_bit           16384  1 i915"""
        
        # Set up mock responses
        self.mock_system.run_command.side_effect = lambda cmd: {
            'lspci -nn -v -d ::0300': 
                CommandResult(True, lspci_output, '', 0),
            'lspci -nn -v -d ::0302': 
                CommandResult(True, '', '', 0),
            'xrandr --verbose': 
                CommandResult(True, xrandr_output, '', 0),
            'lsmod': 
                CommandResult(True, lsmod_output, '', 0),
            'lspci': 
                CommandResult(True, 'Intel Corporation UHD Graphics 620', '', 0),
            'modinfo i915': 
                CommandResult(True, 'version:        5.15.0\nauthor:         Intel Corporation\ndescription:    Intel Graphics\nlicense:        GPL', '', 0),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))
        
        # Mock file_exists
        self.mock_system.file_exists.return_value = True
        
        # Mock read_file
        self.mock_system.read_file.side_effect = lambda path: {
            '/sys/class/drm/card0/device/vendor': '0x8086',
            '/sys/class/drm/card0/device/device': '0x5917',
            '/sys/class/drm/card0/device/uevent': 'DRIVER=i915',
        }.get(path, None)


if __name__ == '__main__':
    unittest.main()