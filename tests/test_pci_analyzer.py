#!/usr/bin/env python3
"""Tests for the PCI Analyzer module.

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

from infenix.hardware.pci_analyzer import PCIAnalyzer
from infenix.interfaces import CommandResult


class TestPCIAnalyzer(unittest.TestCase):
    """Test cases for the PCIAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.analyzer = PCIAnalyzer(self.mock_system)
        
        # Mock the PCI IDs database loading
        self.analyzer.vendor_db = {'8086': 'Intel Corporation', '10de': 'NVIDIA Corporation'}
        self.analyzer.device_db = {
            '8086': {'1234': 'Sample Intel Device'},
            '10de': {'0123': 'Sample NVIDIA Device'}
        }
    
    def test_get_pci_devices(self):
        """Test getting comprehensive PCI device information."""
        # Mock system interface responses
        self._setup_basic_mocks()
        
        # Call the method under test
        result = self.analyzer.get_pci_devices()
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        self.assertGreater(len(result['devices']), 0)
    
    def test_parse_lspci_output(self):
        """Test parsing lspci -mm output."""
        lspci_output = '''00:00.0 "Host bridge" "Intel Corporation" "82G33/G31/P35/P31 Express DRAM Controller" -r02 "Hewlett-Packard Company" "Device 2818"
00:01.0 "PCI bridge" "Intel Corporation" "82G33/G31/P35/P31 Express PCI Express Root Port" -r02 "" ""
01:00.0 "VGA compatible controller" "NVIDIA Corporation" "GF119 [GeForce GT 610]" -ra1 "eVga.com. Corp." "Device 2615"'''
        
        result = self.analyzer._parse_lspci_output(lspci_output)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['address'], '00:00.0')
        self.assertEqual(result[0]['class'], 'Host bridge')
        self.assertEqual(result[0]['vendor'], 'Intel Corporation')
        self.assertEqual(result[0]['device'], '82G33/G31/P35/P31 Express DRAM Controller')
        self.assertEqual(result[0]['subsystem_vendor'], 'Hewlett-Packard Company')
        self.assertEqual(result[0]['subsystem_device'], 'Device 2818')
    
    def test_parse_lspci_detailed(self):
        """Test parsing lspci -vvv output."""
        lspci_detailed = '''00:00.0 Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller (rev 02)
	Subsystem: Hewlett-Packard Company Device 2818
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Status: Cap+ 66MHz- UDF- FastB2B+ ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort+ >SERR- <PERR- INTx-
	Latency: 0
	Capabilities: [e0] Vendor Specific Information: Len=0c <?>
	Kernel driver in use: agpgart-intel
	Kernel modules: intel-agp

00:01.0 PCI bridge: Intel Corporation 82G33/G31/P35/P31 Express PCI Express Root Port (rev 02) (prog-if 00 [Normal decode])
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- >SERR- <PERR- INTx-
	Latency: 0, Cache Line Size: 64 bytes
	Bus: primary=00, secondary=01, subordinate=01, sec-latency=0
	I/O behind bridge: 0000e000-0000efff
	Memory behind bridge: fe900000-fe9fffff
	Prefetchable memory behind bridge: 00000000d0000000-00000000dfffffff
	Secondary status: 66MHz- FastB2B- ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort- <SERR- <PERR-
	BridgeCtl: Parity- SERR- NoISA- VGA+ MAbort- >Reset- FastB2B-
		PriDiscTmr- SecDiscTmr- DiscTmrStat- DiscTmrSERREn-
	Capabilities: [88] Subsystem: Intel Corporation Device 0000
	Capabilities: [80] Power Management version 2
		Flags: PMEClk- DSI- D1- D2- AuxCurrent=0mA PME(D0+,D1-,D2-,D3hot+,D3cold+)
		Status: D0 NoSoftRst+ PME-Enable- DSel=0 DScale=0 PME-
	Capabilities: [90] MSI: Enable- Count=1/1 Maskable- 64bit-
		Address: 00000000  Data: 0000
	Capabilities: [a0] Express (v1) Root Port (Slot+), MSI 00
		DevCap:	MaxPayload 128 bytes, PhantFunc 0, Latency L0s <64ns, L1 <1us
			ExtTag- RBE- FLReset-
		DevCtl:	Report errors: Correctable- Non-Fatal- Fatal- Unsupported-
			RlxdOrd- ExtTag- PhantFunc- AuxPwr- NoSnoop-
			MaxPayload 128 bytes, MaxReadReq 128 bytes
		DevSta:	CorrErr- UncorrErr- FatalErr- UnsuppReq- AuxPwr+ TransPend-
		LnkCap:	Port #1, Speed 2.5GT/s, Width x16, ASPM L0s L1, Latency L0 <256ns, L1 <4us
			ClockPM- Surprise- LLActRep- BwNot-
		LnkCtl:	ASPM Disabled; RCB 64 bytes Disabled- Retrain- CommClk+
			ExtSynch- ClockPM- AutWidDis- BWInt- AutBWInt-
		LnkSta:	Speed 2.5GT/s, Width x16, TrErr- Train- SlotClk+ DLActive- BWMgmt- ABWMgmt-
		SltCap:	AttnBtn- PwrCtrl- MRL- AttnInd- PwrInd- HotPlug- Surprise-
			Slot #0, PowerLimit 75.000W; Interlock- NoCompl+
		SltCtl:	Enable: AttnBtn- PwrFlt- MRL- PresDet- CmdCplt- HPIrq- LinkChg-
			Control: AttnInd Unknown, PwrInd Unknown, Power- Interlock-
		SltSta:	Status: AttnBtn- PowerFlt- MRL- CmdCplt- PresDet+ Interlock-
			Changed: MRL- PresDet- LinkState-
		RootCtl: ErrCorrectable- ErrNon-Fatal- ErrFatal- PMEIntEna- CRSVisible-
		RootCap: CRSVisible-
		RootSta: PME ReqID 0000, PMEStatus- PMEPending-
	Capabilities: [100 v1] Virtual Channel
		Caps:	LPEVC=0 RefClk=100ns PATEntryBits=1
		Arb:	Fixed- WRR32- WRR64- WRR128-
		Ctrl:	ArbSelect=Fixed
		Status:	InProgress-
		VC0:	Caps:	PATOffset=00 MaxTimeSlots=1 RejSnoopTrans-
			Arb:	Fixed- WRR32- WRR64- WRR128- TWRR128- WRR256-
			Ctrl:	Enable+ ID=0 ArbSelect=Fixed TC/VC=ff
			Status:	NegoPending- InProgress-
	Capabilities: [140 v1] Root Complex Link
		Desc:	PortNumber=01 ComponentID=01 EltType=Config
		Link0:	Desc:	TargetPort=00 TargetComponent=01 AssocRCRB- LinkType=MemMapped LinkValid+
			Addr:	00000000fed19000
	Kernel modules: shpchp'''
        
        result = self.analyzer._parse_lspci_detailed(lspci_detailed)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['address'], '00:00.0')
        self.assertEqual(result[0]['description'], 'Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller')
        self.assertEqual(result[0]['driver'], 'agpgart-intel')
        self.assertEqual(result[1]['address'], '00:01.0')
        self.assertEqual(result[1]['description'], 'PCI bridge: Intel Corporation 82G33/G31/P35/P31 Express PCI Express Root Port')
    
    def test_find_devices_without_drivers(self):
        """Test finding PCI devices without drivers."""
        lspci_k_output = '''00:00.0 Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller (rev 02)
	Kernel driver in use: agpgart-intel
	Kernel modules: intel-agp
00:01.0 PCI bridge: Intel Corporation 82G33/G31/P35/P31 Express PCI Express Root Port (rev 02)
	Kernel modules: shpchp
01:00.0 VGA compatible controller: NVIDIA Corporation GF119 [GeForce GT 610] (rev a1)
	Kernel driver in use: nvidia
	Kernel modules: nvidia'''
        
        result = self.analyzer._find_devices_without_drivers(lspci_k_output)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['address'], '00:01.0')
        self.assertEqual(result[0]['description'], 'PCI bridge: Intel Corporation 82G33/G31/P35/P31 Express PCI Express Root Port')
    
    def _setup_basic_mocks(self):
        """Set up basic mocks for system interface."""
        # Mock lspci output
        lspci_output = '''00:00.0 "Host bridge" "Intel Corporation" "82G33/G31/P35/P31 Express DRAM Controller" -r02 "Hewlett-Packard Company" "Device 2818"
00:01.0 "PCI bridge" "Intel Corporation" "82G33/G31/P35/P31 Express PCI Express Root Port" -r02 "" ""
01:00.0 "VGA compatible controller" "NVIDIA Corporation" "GF119 [GeForce GT 610]" -ra1 "eVga.com. Corp." "Device 2615"'''
        
        # Mock lspci -vvv output
        lspci_detailed = '''00:00.0 Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller (rev 02)
	Subsystem: Hewlett-Packard Company Device 2818
	Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr- Stepping- SERR- FastB2B- DisINTx-
	Status: Cap+ 66MHz- UDF- FastB2B+ ParErr- DEVSEL=fast >TAbort- <TAbort- <MAbort+ >SERR- <PERR- INTx-
	Latency: 0
	Capabilities: [e0] Vendor Specific Information: Len=0c <?>
	Kernel driver in use: agpgart-intel
	Kernel modules: intel-agp'''
        
        # Mock lspci -k output
        lspci_k_output = '''00:00.0 Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller (rev 02)
	Kernel driver in use: agpgart-intel
	Kernel modules: intel-agp
00:01.0 PCI bridge: Intel Corporation 82G33/G31/P35/P31 Express PCI Express Root Port (rev 02)
	Kernel modules: shpchp'''
        
        # Mock lspci -n output
        lspci_n_output = '''00:00.0 0600: 8086:29c0 (rev 02)
00:01.0 0604: 8086:29c1 (rev 02)
01:00.0 0300: 10de:104a (rev a1)'''
        
        # Mock kernel version
        kernel_version = '5.15.0-58-generic'
        
        # Set up mock responses
        self.mock_system.run_command.side_effect = lambda cmd: {
            'lspci -mm': 
                CommandResult(True, lspci_output, '', 0),
            'lspci -vvv': 
                CommandResult(True, lspci_detailed, '', 0),
            'lspci -k': 
                CommandResult(True, lspci_k_output, '', 0),
            'lspci -n': 
                CommandResult(True, lspci_n_output, '', 0),
            'uname -r': 
                CommandResult(True, kernel_version, '', 0),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))
        
        # Mock file_exists
        self.mock_system.file_exists.return_value = True
        
        # Mock read_file for PCI IDs database
        self.mock_system.read_file.return_value = '''# PCI ID Database
8086  Intel Corporation
	1234  Sample Intel Device
10de  NVIDIA Corporation
	0123  Sample NVIDIA Device
'''


if __name__ == '__main__':
    unittest.main()