import unittest
from unittest.mock import DEFAULT, patch

from tinel.hardware import get_all_hardware_info


class TestUpdatedGetAllHardwareInfo(unittest.TestCase):

    def test_returns_dictionary(self):
        # Arrange
        with patch.multiple(
            'tinel.hardware',
            CPUAnalyzer=DEFAULT,
            MemoryAnalyzer=DEFAULT,
            StorageAnalyzer=DEFAULT,
            GraphicsAnalyzer=DEFAULT,
            NetworkAnalyzer=DEFAULT,
            PCIAnalyzer=DEFAULT,
            USBAnalyzer=DEFAULT
        ) as mocks:
            mocks['CPUAnalyzer'].return_value.get_cpu_info.return_value = {}
            mocks['MemoryAnalyzer'].return_value.get_memory_info.return_value = {}
            mocks['StorageAnalyzer'].return_value.get_storage_info.return_value = {}
            mocks['GraphicsAnalyzer'].return_value.get_graphics_info.return_value = {}
            mocks['NetworkAnalyzer'].return_value.get_network_info.return_value = {}
            mocks['PCIAnalyzer'].return_value.get_pci_info.return_value = {}
            mocks['USBAnalyzer'].return_value.get_usb_info.return_value = {}

            # Act
            result = get_all_hardware_info()

            # Assert
            self.assertIsInstance(result, dict)

    @patch('tinel.hardware.CPUAnalyzer')
    @patch('tinel.hardware.MemoryAnalyzer')
    def test_handles_analyzer_exception_gracefully(
        self, mock_memory_analyzer, mock_cpu_analyzer
    ):
        # Arrange
        mock_cpu_analyzer.return_value.get_cpu_info.return_value = {'cores': 4}
        mock_memory_analyzer.return_value.get_memory_info.side_effect = \
            Exception("Memory Read Error")

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
