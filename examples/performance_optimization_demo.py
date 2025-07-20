#!/usr/bin/env python3
"""Performance Optimization Demo.

This example demonstrates how to use Infenix's performance optimization
features including resource monitoring, adaptive management, load detection,
and optimized log analysis.

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

import time
import tempfile
from datetime import datetime, timedelta

from infenix.monitoring import (
    ResourceMonitor, 
    AdaptiveResourceManager, 
    LoadDetector, 
    LoadThrottler
)
from infenix.logs import StreamingLogParser, StreamingConfig


def demo_resource_monitoring():
    """Demonstrate resource monitoring capabilities."""
    print("=== Resource Monitoring Demo ===")
    
    # Create resource monitor
    monitor = ResourceMonitor(history_size=10, monitoring_interval=0.5)
    
    # Get current resource usage
    usage = monitor.get_current_usage()
    print(f"Current CPU usage: {usage.cpu_percent:.1f}%")
    print(f"Current memory usage: {usage.memory_percent:.1f}%")
    print(f"Process CPU usage: {usage.process_cpu_percent:.1f}%")
    print(f"Process memory usage: {usage.process_memory_mb:.1f} MB")
    
    # Get system load
    load = monitor.get_system_load()
    print(f"System load (1min): {load.load_1min:.2f}")
    print(f"Normalized load: {load.normalized_load_1min:.2f}")
    
    # Start monitoring for a short period
    print("\nStarting monitoring for 3 seconds...")
    monitor.start_monitoring()
    time.sleep(3)
    monitor.stop_monitoring()
    
    # Get statistics
    stats = monitor.get_usage_stats()
    if stats:
        print(f"Average CPU usage: {stats['cpu_avg']:.1f}%")
        print(f"Peak memory usage: {stats['memory_max']:.1f}%")
        print(f"Samples collected: {stats['samples']}")
    
    print()


def demo_adaptive_management():
    """Demonstrate adaptive resource management."""
    print("=== Adaptive Resource Management Demo ===")
    
    # Create resource monitor and adaptive manager
    monitor = ResourceMonitor()
    manager = AdaptiveResourceManager(monitor)
    
    # Get current resource level
    current_level = manager.get_current_level()
    print(f"Current resource level: {current_level.value}")
    
    # Get adaptive settings for current level
    settings = manager.get_adaptive_settings()
    print(f"Max concurrent operations: {settings['max_concurrent_operations']}")
    print(f"Buffer size: {settings['buffer_size']} bytes")
    print(f"Processing delay: {settings['processing_delay']} seconds")
    print(f"Caching enabled: {settings['enable_caching']}")
    
    # Get status
    status = manager.get_status()
    print(f"Current CPU: {status['current_usage']['cpu_percent']:.1f}%")
    print(f"Current memory: {status['current_usage']['memory_percent']:.1f}%")
    
    print()


def demo_load_detection_and_throttling():
    """Demonstrate load detection and throttling."""
    print("=== Load Detection and Throttling Demo ===")
    
    # Create resource monitor, load detector, and throttler
    monitor = ResourceMonitor()
    detector = LoadDetector(monitor)
    throttler = LoadThrottler(detector)
    
    # Get current load level
    load_level = detector.get_current_load_level()
    print(f"Current load level: {load_level.value}")
    
    # Get load information
    load_info = detector.get_load_info()
    print(f"System load (1min): {load_info['load_1min']:.2f}")
    print(f"Recommended delay: {load_info['recommended_delay']:.3f} seconds")
    print(f"Max concurrent operations: {load_info['max_concurrent_ops']}")
    
    # Demonstrate throttling
    print("\nDemonstrating throttling...")
    if detector.should_throttle():
        print("System is under heavy load - applying throttling")
        throttler.throttle_if_needed()
    else:
        print("System load is normal - no throttling needed")
    
    # Demonstrate operation management
    print(f"Can start operation: {throttler.can_start_operation()}")
    if throttler.start_operation():
        print("Operation started successfully")
        print(f"Active operations: {throttler.get_operation_count()}")
        throttler.finish_operation()
        print("Operation finished")
    
    print()


def demo_optimized_log_analysis():
    """Demonstrate optimized log analysis for large files."""
    print("=== Optimized Log Analysis Demo ===")
    
    # Create a sample log file
    log_content = """Jan 15 10:30:45 server1 kernel: System started
Jan 15 10:30:46 server1 sshd: SSH daemon started
Jan 15 10:30:47 server1 apache: Apache web server started
Jan 15 10:30:48 server1 mysql: MySQL database started
Jan 15 10:30:49 server1 nginx: Nginx proxy started
Jan 15 10:30:50 server1 kernel: All services initialized
"""
    
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_file = f.name
    
    try:
        # Create streaming parser with optimized configuration
        config = StreamingConfig(
            buffer_size=4096,
            batch_size=100,
            enable_compression=True,
            enable_mmap=False  # Disabled for small demo file
        )
        parser = StreamingLogParser(config)
        
        # Parse the log file
        print(f"Parsing log file: {log_file}")
        entries = list(parser.parse_large_file(log_file))
        
        print(f"Parsed {len(entries)} log entries:")
        for entry in entries[:3]:  # Show first 3 entries
            print(f"  {entry.timestamp.strftime('%H:%M:%S')} [{entry.severity}] {entry.message}")
        
        if len(entries) > 3:
            print(f"  ... and {len(entries) - 3} more entries")
        
        # Get parsing statistics
        stats = parser.get_statistics()
        print(f"\nParsing statistics:")
        print(f"  Files processed: {stats['files_processed']}")
        print(f"  Lines processed: {stats['lines_processed']}")
        print(f"  Entries parsed: {stats['entries_parsed']}")
        print(f"  Processing time: {stats['processing_time']:.3f} seconds")
        
        if stats['processing_time'] > 0:
            print(f"  Lines per second: {stats['lines_per_second']:.0f}")
            print(f"  Parse success rate: {stats['parse_success_rate']:.2%}")
        
        # Demonstrate time filtering
        print(f"\nDemonstrating time filtering...")
        start_time = datetime.now() - timedelta(hours=1)
        filtered_entries = list(parser.parse_large_file(log_file, start_time=start_time))
        print(f"Entries in last hour: {len(filtered_entries)}")
        
    finally:
        import os
        os.unlink(log_file)
    
    print()


def demo_integrated_performance_optimization():
    """Demonstrate integrated performance optimization."""
    print("=== Integrated Performance Optimization Demo ===")
    
    # Create all components
    monitor = ResourceMonitor()
    manager = AdaptiveResourceManager(monitor)
    detector = LoadDetector(monitor)
    throttler = LoadThrottler(detector)
    
    # Create streaming parser with adaptive configuration
    def get_adaptive_config():
        """Get streaming configuration based on current resource level."""
        settings = manager.get_adaptive_settings()
        return StreamingConfig(
            buffer_size=settings['buffer_size'],
            batch_size=settings['max_concurrent_operations'] * 100,
            max_workers=settings['max_concurrent_operations'],
            enable_mmap=settings['enable_caching']
        )
    
    config = get_adaptive_config()
    parser = StreamingLogParser(config)
    
    print(f"Current resource level: {manager.get_current_level().value}")
    print(f"Adaptive buffer size: {config.buffer_size} bytes")
    print(f"Adaptive batch size: {config.batch_size}")
    print(f"Adaptive max workers: {config.max_workers}")
    
    # Simulate processing with throttling
    print(f"\nSimulating log processing with adaptive throttling...")
    
    for i in range(5):
        if throttler.can_start_operation():
            if throttler.start_operation():
                print(f"Processing batch {i+1}...")
                
                # Apply adaptive delay based on system load
                throttler.adaptive_sleep(0.1)
                
                # Simulate some work
                time.sleep(0.1)
                
                throttler.finish_operation()
                print(f"Batch {i+1} completed")
            else:
                print(f"Cannot start batch {i+1} - system at capacity")
        else:
            print(f"Waiting for capacity to process batch {i+1}...")
            throttler.wait_for_capacity(timeout=1.0)
    
    # Get final statistics
    throttle_stats = throttler.get_throttle_stats()
    print(f"\nThrottling statistics:")
    print(f"  Current operations: {throttle_stats['current_operations']}")
    print(f"  Max operations: {throttle_stats['max_operations']}")
    print(f"  Is throttling: {throttle_stats['is_throttling']}")
    
    print()


def main():
    """Run all performance optimization demos."""
    print("Infenix Performance Optimization Demo")
    print("=" * 50)
    print()
    
    try:
        demo_resource_monitoring()
        demo_adaptive_management()
        demo_load_detection_and_throttling()
        demo_optimized_log_analysis()
        demo_integrated_performance_optimization()
        
        print("All demos completed successfully!")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()