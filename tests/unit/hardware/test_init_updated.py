import unittest
from unittest.mock import patch, MagicMock
from tinel.hardware import get_all_hardware_info

class TestUpdatedGetAllHardwareInfo(unittest.TestCase):

    @patch('tinel.hardware.CPUAnalyzer')
    @patch('tinel.hardware.MemoryAnalyzer')
    @patch('tinel.hardware.StorageAnalyzer')
    @patch('tinel.hardware.GraphicsAnalyzer')
    @patch('tinel.hardware.NetworkAnalyzer')
    @patch('tinel.hardware.PCIAnalyzer')
    @patch('tinel.hardware.USBAnalyzer')
    def test_returns_dictionary(self, mock_cpu, mock_memory, mock_storage, mock_graphics, mock_network, mock_pci, mock_usb):
        # Arrange
        mock_cpu.return_value.get_cpu_info.return_value = {}
        mock_memory.return_value.get_memory_info.return_value = {}
        mock_storage.return_value.get_storage_info.return_value = {}
        mock_graphics.return_value.get_graphics_info.return_value = {}
        mock_network.return_value.get_network_info.return_value = {}
        mock_pci.return_value.get_pci_info.return_value = {}
        mock_usb.return_value.get_usb_info.return_value = {}

        # Act
        result = get_all_hardware_info()

        # Assert
        self.assertIsInstance(result, dict)

    @patch('tinel.hardware.CPUAnalyzer')
    @patch('tinel.hardware.MemoryAnalyzer')
    def test_handles_analyzer_exception_gracefully(self, mock_memory_analyzer, mock_cpu_analyzer):
        # Arrange
        mock_cpu_analyzer.return_value.get_cpu_info.return_value = {'cores': 4}
        mock_memory_analyzer.return_value.get_memory_info.side_effect = Exception("Memory Read Error")

        # Act
        result = get_all_hardware_info()

        # Assert
        self.assertIn('cpu', result)
        self.assertEqual(result['cpu'], {'cores': 4})
        self.assertIn('memory', result)
        self.assertIn('error', result['memory'])
        self.assertIn("Memory Read Error", result['memory']['error'])

if __name__ == '__main__':
    unittest.main()