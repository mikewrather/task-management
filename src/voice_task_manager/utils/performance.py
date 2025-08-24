"""
Performance monitoring utilities for voice task manager

Provides decorators and utilities for tracking performance metrics
in production deployments.
"""

import time
import functools
import psutil
import os
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Individual performance measurement"""
    operation: str
    duration_ms: float
    timestamp: datetime
    memory_mb: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection
    
    Usage:
        monitor = PerformanceMonitor()
        
        @monitor.track_performance
        def slow_operation():
            time.sleep(1)
        
        # Get metrics
        print(monitor.get_summary())
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize performance monitor
        
        Args:
            enabled: Whether to actually collect metrics (disable in production if needed)
        """
        self.enabled = enabled
        self.metrics: Dict[str, list[PerformanceMetric]] = {}
        self._process = psutil.Process(os.getpid()) if enabled else None
    
    def track_performance(self, 
                         operation_name: Optional[str] = None,
                         track_memory: bool = False) -> Callable:
        """
        Decorator to track function performance
        
        Args:
            operation_name: Custom name for the operation (defaults to function name)
            track_memory: Whether to track memory usage
        """
        def decorator(func: Callable) -> Callable:
            if not self.enabled:
                return func
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                name = operation_name or func.__name__
                return self._measure_operation(name, func, track_memory, *args, **kwargs)
            
            return wrapper
        return decorator
    
    def _measure_operation(self, 
                          name: str, 
                          func: Callable, 
                          track_memory: bool,
                          *args, **kwargs) -> Any:
        """Internal method to measure operation performance"""
        if not self.enabled:
            return func(*args, **kwargs)
        
        # Pre-execution measurements
        start_time = time.time()
        start_memory = None
        if track_memory and self._process:
            start_memory = self._process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Post-execution measurements
            duration_ms = (time.time() - start_time) * 1000
            memory_mb = None
            
            if track_memory and self._process and start_memory:
                end_memory = self._process.memory_info().rss / 1024 / 1024  # MB
                memory_mb = end_memory - start_memory
            
            # Record metric
            metric = PerformanceMetric(
                operation=name,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                memory_mb=memory_mb,
                metadata={
                    'success': True,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
            
            self._record_metric(metric)
            return result
            
        except Exception as e:
            # Record failed operation
            duration_ms = (time.time() - start_time) * 1000
            metric = PerformanceMetric(
                operation=name,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                metadata={
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
            self._record_metric(metric)
            raise
    
    def _record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        if metric.operation not in self.metrics:
            self.metrics[metric.operation] = []
        self.metrics[metric.operation].append(metric)
    
    def get_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance summary for all tracked operations
        
        Returns:
            Dictionary with performance statistics per operation
        """
        summary = {}
        
        for operation, metrics in self.metrics.items():
            if not metrics:
                continue
            
            durations = [m.duration_ms for m in metrics]
            successful_metrics = [m for m in metrics if m.metadata.get('success', True)]
            
            summary[operation] = {
                'total_calls': len(metrics),
                'successful_calls': len(successful_metrics),
                'success_rate': len(successful_metrics) / len(metrics) if metrics else 0,
                'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
                'min_duration_ms': min(durations) if durations else 0,
                'max_duration_ms': max(durations) if durations else 0,
                'total_duration_ms': sum(durations),
                'p95_duration_ms': self._percentile(durations, 95) if durations else 0,
                'p99_duration_ms': self._percentile(durations, 99) if durations else 0,
            }
            
            # Add memory stats if available
            memory_deltas = [m.memory_mb for m in metrics if m.memory_mb is not None]
            if memory_deltas:
                summary[operation].update({
                    'avg_memory_delta_mb': sum(memory_deltas) / len(memory_deltas),
                    'max_memory_delta_mb': max(memory_deltas),
                    'total_memory_delta_mb': sum(memory_deltas)
                })
        
        return summary
    
    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile of a list"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_summary(self):
        """Print a formatted performance summary"""
        summary = self.get_summary()
        
        if not summary:
            print("No performance metrics collected")
            return
        
        print("\\n" + "="*80)
        print(" PERFORMANCE SUMMARY")
        print("="*80)
        
        for operation, stats in summary.items():
            print(f"\\n📊 {operation}")
            print(f"   Calls: {stats['total_calls']} ({stats['success_rate']*100:.1f}% success)")
            print(f"   Timing: avg={stats['avg_duration_ms']:.1f}ms, "
                  f"p95={stats['p95_duration_ms']:.1f}ms, "
                  f"max={stats['max_duration_ms']:.1f}ms")
            
            if 'avg_memory_delta_mb' in stats:
                print(f"   Memory: avg={stats['avg_memory_delta_mb']:.1f}MB, "
                      f"max={stats['max_memory_delta_mb']:.1f}MB")
    
    def export_metrics(self, filepath: Path):
        """Export metrics to JSON file"""
        import json
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'raw_metrics': {}
        }
        
        # Convert metrics to serializable format
        for operation, metrics in self.metrics.items():
            export_data['raw_metrics'][operation] = [
                {
                    'operation': m.operation,
                    'duration_ms': m.duration_ms,
                    'timestamp': m.timestamp.isoformat(),
                    'memory_mb': m.memory_mb,
                    'metadata': m.metadata
                }
                for m in metrics
            ]
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def clear_metrics(self):
        """Clear all collected metrics"""
        self.metrics.clear()
    
    def get_operation_metrics(self, operation: str) -> list[PerformanceMetric]:
        """Get raw metrics for a specific operation"""
        return self.metrics.get(operation, [])


# Global monitor instance for easy use
_global_monitor = PerformanceMonitor()

def track_performance(operation_name: Optional[str] = None, 
                     track_memory: bool = False) -> Callable:
    """
    Convenience decorator using global monitor
    
    Usage:
        @track_performance("database_query")
        def query_database():
            # ... database operation
    """
    return _global_monitor.track_performance(operation_name, track_memory)


def get_performance_summary() -> Dict[str, Dict[str, Any]]:
    """Get summary from global monitor"""
    return _global_monitor.get_summary()


def print_performance_summary():
    """Print summary from global monitor"""
    _global_monitor.print_summary()


def clear_performance_metrics():
    """Clear global monitor metrics"""
    _global_monitor.clear_metrics()


# Example usage and integration helpers
class PerformanceIntegration:
    """Helper class for integrating performance monitoring into existing code"""
    
    @staticmethod
    def enhance_voice_processor(processor_class):
        """
        Enhance VoiceProcessor with performance monitoring
        
        Usage:
            processor = VoiceProcessor()
            PerformanceIntegration.enhance_voice_processor(processor)
        """
        # Add performance monitoring to key methods
        key_methods = [
            'discover_voice_files',
            'process_all_files', 
            'process_single_file',
            '_transcribe_audio',
            'create_task'
        ]
        
        for method_name in key_methods:
            if hasattr(processor_class, method_name):
                original_method = getattr(processor_class, method_name)
                enhanced_method = _global_monitor.track_performance(
                    f"VoiceProcessor.{method_name}",
                    track_memory=True
                )(original_method)
                setattr(processor_class, method_name, enhanced_method)
    
    @staticmethod
    def enhance_database(database_class):
        """
        Enhance VoiceDatabase with performance monitoring
        
        Usage:
            db = VoiceDatabase()
            PerformanceIntegration.enhance_database(db)
        """
        db_methods = [
            'save_voice_file',
            'get_voice_file',
            'get_all_voice_files',
            'save_task',
            'get_task',
            'get_processing_stats'
        ]
        
        for method_name in db_methods:
            if hasattr(database_class, method_name):
                original_method = getattr(database_class, method_name)
                enhanced_method = _global_monitor.track_performance(
                    f"Database.{method_name}"
                )(original_method)
                setattr(database_class, method_name, enhanced_method)


if __name__ == "__main__":
    # Example usage
    monitor = PerformanceMonitor()
    
    @monitor.track_performance("example_operation", track_memory=True)
    def example_function():
        time.sleep(0.1)  # Simulate work
        return "done"
    
    # Run some operations
    for i in range(5):
        example_function()
    
    # Print summary
    monitor.print_summary()