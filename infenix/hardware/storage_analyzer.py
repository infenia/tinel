#!/usr/bin/env python3
"""Enhanced Storage Analysis Module.

This module provides detailed storage information gathering including filesystem
performance metrics, storage health analysis, and optimization recommendations.

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

import re
import json
from typing import Any, Dict, List, Optional, Tuple

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class StorageAnalyzer:
    """Enhanced storage analyzer with detailed information gathering."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize storage analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get comprehensive storage information.
        
        Returns:
            Dictionary containing detailed storage information
        """
        info: Dict[str, Any] = {}
        
        # Get basic storage info
        info.update(self._get_basic_storage_info())
        
        # Get detailed disk information
        info.update(self._get_detailed_disk_info())
        
        # Get filesystem information
        info.update(self._get_filesystem_info())
        
        # Get storage performance metrics
        info.update(self._get_storage_performance_metrics())
        
        # Get storage health information
        info.update(self._get_storage_health_info())
        
        # Get storage optimization analysis
        info.update(self._analyze_storage_optimization())
        
        return info
    
    def _get_basic_storage_info(self) -> Dict[str, Any]:
        """Get basic storage information using lsblk."""
        info: Dict[str, Any] = {}
        
        # Get block device information using lsblk
        lsblk_result = self.system.run_command(['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,SERIAL,VENDOR,ROTA,TRAN'])
        if lsblk_result.success:
            try:
                info['lsblk'] = json.loads(lsblk_result.stdout)
            except json.JSONDecodeError:
                info['lsblk_error'] = 'Failed to parse lsblk JSON output'
        else:
            info['lsblk_error'] = lsblk_result.error or 'Failed to run lsblk'
        
        # Get disk usage information using df
        df_result = self.system.run_command(['df', '-h'])
        if df_result.success:
            info['df'] = df_result.stdout
            info.update(self._parse_df_output(df_result.stdout))
        else:
            info['df_error'] = df_result.error or 'Failed to run df'
        
        return info
    
    def _get_detailed_disk_info(self) -> Dict[str, Any]:
        """Get detailed disk information."""
        info: Dict[str, Any] = {}
        disks = []
        
        # Get list of physical disks
        lsblk_result = self.system.run_command(['lsblk', '-d', '-n', '-o', 'NAME'])
        if lsblk_result.success:
            disk_names = lsblk_result.stdout.strip().split('\n')
            
            for disk_name in disk_names:
                disk_info = self._get_disk_details(disk_name)
                if disk_info:
                    disks.append(disk_info)
        
        if disks:
            info['disks'] = disks
            info['disk_count'] = len(disks)
        
        return info
    
    def _get_disk_details(self, disk_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific disk."""
        disk_info: Dict[str, Any] = {'name': disk_name}
        
        # Get disk details using hdparm
        hdparm_result = self.system.run_command(['sudo', 'hdparm', '-i', f'/dev/{disk_name}'])
        if hdparm_result.success and 'bad/missing sense data' not in hdparm_result.stderr:
            disk_info['hdparm'] = hdparm_result.stdout
            disk_info.update(self._parse_hdparm_output(hdparm_result.stdout))
        
        # Get disk details using smartctl
        smartctl_result = self.system.run_command(['sudo', 'smartctl', '-i', f'/dev/{disk_name}'])
        if smartctl_result.success:
            disk_info['smartctl'] = smartctl_result.stdout
            disk_info.update(self._parse_smartctl_output(smartctl_result.stdout))
        
        # Get disk details using udevadm
        udevadm_result = self.system.run_command(['udevadm', 'info', '--query=property', f'/dev/{disk_name}'])
        if udevadm_result.success:
            disk_info['udevadm'] = udevadm_result.stdout
            disk_info.update(self._parse_udevadm_output(udevadm_result.stdout))
        
        # Get partition information
        partitions = self._get_partition_info(disk_name)
        if partitions:
            disk_info['partitions'] = partitions
        
        return disk_info
    
    def _get_partition_info(self, disk_name: str) -> List[Dict[str, Any]]:
        """Get partition information for a specific disk."""
        partitions = []
        
        # Get partition list using lsblk
        lsblk_result = self.system.run_command(['lsblk', '-J', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL', f'/dev/{disk_name}'])
        if lsblk_result.success:
            try:
                lsblk_data = json.loads(lsblk_result.stdout)
                if 'blockdevices' in lsblk_data and lsblk_data['blockdevices']:
                    for device in lsblk_data['blockdevices']:
                        if 'children' in device:
                            for partition in device['children']:
                                part_info = {
                                    'name': partition.get('name', ''),
                                    'size': partition.get('size', ''),
                                    'fstype': partition.get('fstype', ''),
                                    'mountpoint': partition.get('mountpoint', ''),
                                    'label': partition.get('label', '')
                                }
                                partitions.append(part_info)
            except json.JSONDecodeError:
                pass
        
        return partitions
    
    def _get_filesystem_info(self) -> Dict[str, Any]:
        """Get filesystem information."""
        info: Dict[str, Any] = {}
        filesystems = []
        
        # Get mounted filesystems
        mount_result = self.system.run_command(['mount'])
        if mount_result.success:
            for line in mount_result.stdout.strip().split('\n'):
                fs_info = self._parse_mount_line(line)
                if fs_info:
                    filesystems.append(fs_info)
        
        if filesystems:
            info['filesystems'] = filesystems
            info['filesystem_count'] = len(filesystems)
        
        # Get filesystem usage information
        df_result = self.system.run_command(['df', '-T'])
        if df_result.success:
            info['filesystem_usage'] = self._parse_df_types(df_result.stdout)
        
        return info
    
    def _get_storage_performance_metrics(self) -> Dict[str, Any]:
        """Get storage performance metrics."""
        info: Dict[str, Any] = {}
        
        # Get I/O statistics
        iostat_result = self.system.run_command(['iostat', '-x', '-d'])
        if iostat_result.success:
            info['iostat'] = iostat_result.stdout
            info.update(self._parse_iostat_output(iostat_result.stdout))
        
        # Get filesystem performance metrics
        for fs_type in ['ext4', 'xfs', 'btrfs']:
            metrics = self._get_fs_specific_metrics(fs_type)
            if metrics:
                info[f'{fs_type}_metrics'] = metrics
        
        return info
    
    def _get_fs_specific_metrics(self, fs_type: str) -> Optional[Dict[str, Any]]:
        """Get filesystem-specific performance metrics."""
        metrics = {}
        
        if fs_type == 'ext4':
            # Get ext4 filesystem metrics
            tune2fs_result = self.system.run_command(['sudo', 'tune2fs', '-l', '/dev/sda1'])
            if tune2fs_result.success:
                metrics['tune2fs'] = tune2fs_result.stdout
                metrics.update(self._parse_tune2fs_output(tune2fs_result.stdout))
        
        elif fs_type == 'xfs':
            # Get XFS filesystem metrics
            xfs_info_result = self.system.run_command(['xfs_info', '/'])
            if xfs_info_result.success:
                metrics['xfs_info'] = xfs_info_result.stdout
        
        elif fs_type == 'btrfs':
            # Get BTRFS filesystem metrics
            btrfs_result = self.system.run_command(['sudo', 'btrfs', 'filesystem', 'usage', '/'])
            if btrfs_result.success:
                metrics['btrfs_usage'] = btrfs_result.stdout
        
        return metrics if metrics else None
    
    def _get_storage_health_info(self) -> Dict[str, Any]:
        """Get storage health information."""
        info: Dict[str, Any] = {}
        health_info = []
        
        # Get list of physical disks
        lsblk_result = self.system.run_command(['lsblk', '-d', '-n', '-o', 'NAME'])
        if lsblk_result.success:
            disk_names = lsblk_result.stdout.strip().split('\n')
            
            for disk_name in disk_names:
                # Skip loop devices, ram devices, etc.
                if disk_name.startswith(('loop', 'ram')):
                    continue
                
                # Get SMART health information
                smart_result = self.system.run_command(['sudo', 'smartctl', '-H', f'/dev/{disk_name}'])
                if smart_result.success:
                    health_status = self._parse_smart_health(smart_result.stdout)
                    
                    # Get SMART attributes
                    smart_attrs_result = self.system.run_command(['sudo', 'smartctl', '-A', f'/dev/{disk_name}'])
                    smart_attrs = {}
                    if smart_attrs_result.success:
                        smart_attrs = self._parse_smart_attributes(smart_attrs_result.stdout)
                    
                    health_info.append({
                        'disk': disk_name,
                        'health_status': health_status,
                        'smart_attributes': smart_attrs
                    })
        
        if health_info:
            info['health_info'] = health_info
        
        return info
    
    def _analyze_storage_optimization(self) -> Dict[str, Any]:
        """Analyze storage for optimization opportunities."""
        info: Dict[str, Any] = {}
        recommendations = []
        
        # Check filesystem usage
        df_result = self.system.run_command(['df', '-h'])
        if df_result.success:
            high_usage_filesystems = self._check_high_usage_filesystems(df_result.stdout)
            for fs in high_usage_filesystems:
                recommendations.append({
                    'type': 'capacity',
                    'issue': f'High usage on {fs["mountpoint"]}: {fs["usage_percent"]}%',
                    'recommendation': 'Consider freeing up space or expanding the filesystem',
                    'severity': 'high' if int(fs["usage_percent"]) > 90 else 'medium'
                })
        
        # Check for fragmentation
        for fs_type in ['ext4', 'xfs']:
            fragmentation = self._check_fragmentation(fs_type)
            if fragmentation and fragmentation.get('fragmented', False):
                recommendations.append({
                    'type': 'performance',
                    'issue': f'Fragmentation detected on {fs_type} filesystem',
                    'recommendation': f'Consider defragmenting the {fs_type} filesystem',
                    'command': self._get_defrag_command(fs_type),
                    'severity': 'medium'
                })
        
        # Check for suboptimal mount options
        mount_result = self.system.run_command(['mount'])
        if mount_result.success:
            suboptimal_mounts = self._check_mount_options(mount_result.stdout)
            for mount in suboptimal_mounts:
                recommendations.append({
                    'type': 'performance',
                    'issue': f'Suboptimal mount options for {mount["mountpoint"]}',
                    'recommendation': f'Consider adding {mount["missing_option"]} option',
                    'command': mount.get('command', ''),
                    'severity': 'low'
                })
        
        # Check for failing disks
        health_info = info.get('health_info', [])
        for disk in health_info:
            if disk.get('health_status', '') == 'FAILED':
                recommendations.append({
                    'type': 'reliability',
                    'issue': f'Disk {disk["disk"]} is failing',
                    'recommendation': 'Replace the disk as soon as possible',
                    'severity': 'critical'
                })
        
        info['optimization_recommendations'] = recommendations
        return info
    
    def _parse_df_output(self, df_output: str) -> Dict[str, Any]:
        """Parse df command output."""
        info: Dict[str, Any] = {}
        filesystems = []
        
        lines = df_output.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    fs_info = {
                        'filesystem': parts[0],
                        'size': parts[1],
                        'used': parts[2],
                        'available': parts[3],
                        'use_percent': parts[4],
                        'mountpoint': parts[5]
                    }
                    filesystems.append(fs_info)
        
        if filesystems:
            info['filesystems'] = filesystems
        
        return info
    
    def _parse_df_types(self, df_output: str) -> List[Dict[str, Any]]:
        """Parse df -T command output to get filesystem types."""
        filesystems = []
        
        lines = df_output.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 7:
                    fs_info = {
                        'filesystem': parts[0],
                        'type': parts[1],
                        'size': parts[2],
                        'used': parts[3],
                        'available': parts[4],
                        'use_percent': parts[5],
                        'mountpoint': parts[6]
                    }
                    filesystems.append(fs_info)
        
        return filesystems
    
    def _parse_hdparm_output(self, hdparm_output: str) -> Dict[str, Any]:
        """Parse hdparm output."""
        info: Dict[str, Any] = {}
        
        # Extract model
        model_match = re.search(r'Model=(.+?),', hdparm_output)
        if model_match:
            info['model'] = model_match.group(1).strip()
        
        # Extract serial number
        serial_match = re.search(r'SerialNo=(.+?)\n', hdparm_output)
        if serial_match:
            info['serial'] = serial_match.group(1).strip()
        
        # Extract firmware version
        fw_match = re.search(r'FwRev=(.+?)\n', hdparm_output)
        if fw_match:
            info['firmware'] = fw_match.group(1).strip()
        
        return info
    
    def _parse_smartctl_output(self, smartctl_output: str) -> Dict[str, Any]:
        """Parse smartctl output."""
        info: Dict[str, Any] = {}
        
        # Extract model family
        family_match = re.search(r'Model Family:\s*(.+)', smartctl_output)
        if family_match:
            info['model_family'] = family_match.group(1).strip()
        
        # Extract device model
        model_match = re.search(r'Device Model:\s*(.+)', smartctl_output)
        if model_match:
            info['device_model'] = model_match.group(1).strip()
        
        # Extract serial number
        serial_match = re.search(r'Serial Number:\s*(.+)', smartctl_output)
        if serial_match:
            info['serial_number'] = serial_match.group(1).strip()
        
        # Extract firmware version
        fw_match = re.search(r'Firmware Version:\s*(.+)', smartctl_output)
        if fw_match:
            info['firmware_version'] = fw_match.group(1).strip()
        
        # Extract capacity
        capacity_match = re.search(r'User Capacity:\s*(.+)', smartctl_output)
        if capacity_match:
            info['capacity'] = capacity_match.group(1).strip()
        
        # Extract rotation rate
        rotation_match = re.search(r'Rotation Rate:\s*(.+)', smartctl_output)
        if rotation_match:
            rotation = rotation_match.group(1).strip()
            info['rotation_rate'] = rotation
            info['is_ssd'] = 'Solid State Device' in rotation
        
        # Extract SATA version
        sata_match = re.search(r'SATA Version is:\s*(.+)', smartctl_output)
        if sata_match:
            info['sata_version'] = sata_match.group(1).strip()
        
        return info
    
    def _parse_udevadm_output(self, udevadm_output: str) -> Dict[str, Any]:
        """Parse udevadm output."""
        info: Dict[str, Any] = {}
        
        for line in udevadm_output.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                if key == 'ID_MODEL':
                    info['udev_model'] = value
                elif key == 'ID_SERIAL':
                    info['udev_serial'] = value
                elif key == 'ID_TYPE':
                    info['udev_type'] = value
                elif key == 'ID_BUS':
                    info['udev_bus'] = value
                elif key == 'ID_PATH':
                    info['udev_path'] = value
        
        return info
    
    def _parse_mount_line(self, mount_line: str) -> Optional[Dict[str, Any]]:
        """Parse a single line from mount output."""
        parts = mount_line.split()
        if len(parts) >= 6:
            return {
                'device': parts[0],
                'mountpoint': parts[2],
                'fstype': parts[4],
                'options': parts[5].strip('()')
            }
        return None
    
    def _parse_iostat_output(self, iostat_output: str) -> Dict[str, Any]:
        """Parse iostat output."""
        info: Dict[str, Any] = {}
        devices = []
        
        lines = iostat_output.strip().split('\n')
        header_line = None
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'Device' in line and 'r/s' in line:
                header_line = i
                break
        
        if header_line is not None and header_line + 1 < len(lines):
            headers = lines[header_line].split()
            
            for line in lines[header_line + 1:]:
                if line.strip():
                    values = line.split()
                    if len(values) >= len(headers):
                        device_info = {'device': values[0]}
                        for i in range(1, len(headers)):
                            device_info[headers[i]] = values[i]
                        devices.append(device_info)
        
        if devices:
            info['io_stats'] = devices
        
        return info
    
    def _parse_tune2fs_output(self, tune2fs_output: str) -> Dict[str, Any]:
        """Parse tune2fs output."""
        info: Dict[str, Any] = {}
        
        # Extract filesystem features
        features_match = re.search(r'Filesystem features:\s*(.+)', tune2fs_output)
        if features_match:
            info['features'] = features_match.group(1).strip().split()
        
        # Extract inode count
        inode_match = re.search(r'Inode count:\s*(.+)', tune2fs_output)
        if inode_match:
            info['inode_count'] = int(inode_match.group(1).strip())
        
        # Extract block count
        block_match = re.search(r'Block count:\s*(.+)', tune2fs_output)
        if block_match:
            info['block_count'] = int(block_match.group(1).strip())
        
        # Extract free blocks
        free_blocks_match = re.search(r'Free blocks:\s*(.+)', tune2fs_output)
        if free_blocks_match:
            info['free_blocks'] = int(free_blocks_match.group(1).strip())
        
        # Extract free inodes
        free_inodes_match = re.search(r'Free inodes:\s*(.+)', tune2fs_output)
        if free_inodes_match:
            info['free_inodes'] = int(free_inodes_match.group(1).strip())
        
        # Calculate usage percentages
        if 'block_count' in info and 'free_blocks' in info:
            info['block_usage_percent'] = round(
                (info['block_count'] - info['free_blocks']) / info['block_count'] * 100, 2
            )
        
        if 'inode_count' in info and 'free_inodes' in info:
            info['inode_usage_percent'] = round(
                (info['inode_count'] - info['free_inodes']) / info['inode_count'] * 100, 2
            )
        
        return info
    
    def _parse_smart_health(self, smart_output: str) -> str:
        """Parse SMART health status."""
        if 'PASSED' in smart_output:
            return 'PASSED'
        elif 'FAILED' in smart_output:
            return 'FAILED'
        else:
            return 'UNKNOWN'
    
    def _parse_smart_attributes(self, smart_output: str) -> Dict[str, Any]:
        """Parse SMART attributes."""
        attributes = {}
        
        # Find the attributes table
        table_start = smart_output.find('ID# ATTRIBUTE_NAME')
        if table_start != -1:
            lines = smart_output[table_start:].strip().split('\n')
            
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 10:
                    try:
                        attr_id = int(parts[0])
                        attr_name = parts[1]
                        attr_value = int(parts[3])
                        attr_worst = int(parts[4])
                        attr_thresh = int(parts[5])
                        attr_raw = parts[9]
                        
                        attributes[attr_name] = {
                            'id': attr_id,
                            'value': attr_value,
                            'worst': attr_worst,
                            'threshold': attr_thresh,
                            'raw': attr_raw
                        }
                    except (ValueError, IndexError):
                        continue
        
        return attributes
    
    def _check_high_usage_filesystems(self, df_output: str) -> List[Dict[str, Any]]:
        """Check for filesystems with high usage."""
        high_usage = []
        
        lines = df_output.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    usage_percent = parts[4].rstrip('%')
                    try:
                        usage = int(usage_percent)
                        if usage > 80:
                            high_usage.append({
                                'filesystem': parts[0],
                                'mountpoint': parts[5],
                                'usage_percent': usage_percent
                            })
                    except ValueError:
                        continue
        
        return high_usage
    
    def _check_fragmentation(self, fs_type: str) -> Optional[Dict[str, Any]]:
        """Check filesystem fragmentation."""
        if fs_type == 'ext4':
            # Check ext4 fragmentation using e4defrag
            e4defrag_result = self.system.run_command(['sudo', 'e4defrag', '-c', '/'])
            if e4defrag_result.success:
                fragmentation_score = self._parse_e4defrag_output(e4defrag_result.stdout)
                return {
                    'fragmented': fragmentation_score > 30,
                    'score': fragmentation_score
                }
        
        return None
    
    def _parse_e4defrag_output(self, e4defrag_output: str) -> int:
        """Parse e4defrag output to get fragmentation score."""
        score_match = re.search(r'Fragmentation score:\s*(\d+)', e4defrag_output)
        if score_match:
            return int(score_match.group(1))
        return 0
    
    def _check_mount_options(self, mount_output: str) -> List[Dict[str, Any]]:
        """Check for suboptimal mount options."""
        suboptimal_mounts = []
        
        for line in mount_output.strip().split('\n'):
            if 'ext4' in line or 'xfs' in line:
                mount_info = self._parse_mount_line(line)
                if mount_info:
                    options = mount_info['options'].split(',')
                    
                    # Check for noatime option
                    if 'noatime' not in options and 'relatime' not in options:
                        suboptimal_mounts.append({
                            'mountpoint': mount_info['mountpoint'],
                            'missing_option': 'noatime',
                            'command': f"sudo mount -o remount,noatime {mount_info['mountpoint']}"
                        })
                    
                    # Check for discard option for SSDs
                    device = mount_info['device']
                    if self._is_ssd(device) and 'discard' not in options:
                        suboptimal_mounts.append({
                            'mountpoint': mount_info['mountpoint'],
                            'missing_option': 'discard',
                            'command': f"sudo mount -o remount,discard {mount_info['mountpoint']}"
                        })
        
        return suboptimal_mounts
    
    def _is_ssd(self, device: str) -> bool:
        """Check if a device is an SSD."""
        # Extract the base device name
        base_device = device.split('/')[-1]
        if base_device.startswith(('sd', 'nvme')):
            base_device = re.sub(r'\d+$', '', base_device)
            
            # Check rotation flag in /sys
            rotational = self.system.read_file(f'/sys/block/{base_device}/queue/rotational')
            if rotational == '0':
                return True
        
        return False
    
    def _get_defrag_command(self, fs_type: str) -> str:
        """Get the appropriate defragmentation command for a filesystem type."""
        if fs_type == 'ext4':
            return 'sudo e4defrag /'
        elif fs_type == 'xfs':
            return 'sudo xfs_fsr'
        else:
            return ''