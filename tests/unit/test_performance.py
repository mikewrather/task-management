"""
Performance tests for voice task manager package

Tests key performance characteristics:
- Database query performance
- File processing throughput  
- Memory usage patterns
- Concurrent operation handling
"""

import pytest
import time
import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory

from voice_task_manager.models.voice_file import VoiceFile
from voice_task_manager.models.task import Task  
from voice_task_manager.utils.database import VoiceDatabase
from voice_task_manager.core.processor import VoiceProcessor


class TestDatabasePerformance:
    """Test database operation performance"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for performance testing"""
        with TemporaryDirectory() as temp_dir:
            db = VoiceDatabase(Path(temp_dir))
            yield db
    
    def test_bulk_insert_performance(self, temp_db):
        """Test performance of bulk voice file insertions"""
        num_files = 1000
        voice_files = []
        
        # Generate test data
        for i in range(num_files):
            voice_file = VoiceFile(
                file_id=f"test_file_{i:04d}",
                file_size=1024 * (i % 10 + 1),  # Vary sizes
                content_type="audio/m4a",
                transcript=f"Test transcript {i}" if i % 3 == 0 else None,
                metadata={"batch": "performance_test", "index": i}
            )
            if i % 5 == 0:  # Mark some as completed
                voice_file.mark_completed(f"Transcript {i}", f"https://notion.so/task_{i}")
            voice_files.append(voice_file)
        
        # Time bulk insertion
        start_time = time.time()
        for voice_file in voice_files:
            temp_db.save_voice_file(voice_file)
        insertion_time = time.time() - start_time
        
        # Performance assertions
        assert insertion_time < 10.0  # Should complete in under 10 seconds
        assert insertion_time / num_files < 0.01  # Less than 10ms per file
        
        # Verify all files were saved
        all_files = temp_db.get_all_voice_files()
        assert len(all_files) == num_files
        
        print(f"\\nBulk insert performance: {num_files} files in {insertion_time:.2f}s ({insertion_time/num_files*1000:.1f}ms per file)")
    
    def test_query_performance_with_large_dataset(self, temp_db):
        """Test query performance with larger dataset"""
        # Create test dataset
        num_files = 500
        for i in range(num_files):
            voice_file = VoiceFile(
                file_id=f"query_test_{i:03d}",
                file_size=2048 * (i % 20 + 1),
                transcript=f"Query test transcript {i}" if i % 2 == 0 else None
            )
            if i % 4 == 0:
                voice_file.mark_completed(f"Transcript {i}", f"https://notion.so/task_{i}")
            temp_db.save_voice_file(voice_file)
        
        # Test different query patterns
        queries_to_test = [
            ("get_all_voice_files", lambda: temp_db.get_all_voice_files()),
            ("get_processing_stats", lambda: temp_db.get_processing_stats()),
            ("date_range_query", lambda: temp_db.get_files_by_date_range(
                datetime.now() - timedelta(days=1), datetime.now()
            )),
        ]
        
        for query_name, query_func in queries_to_test:
            start_time = time.time()
            result = query_func()
            query_time = time.time() - start_time
            
            # Performance assertions
            assert query_time < 1.0  # Queries should complete in under 1 second
            print(f"{query_name}: {query_time:.3f}s")
    
    def test_concurrent_database_access(self, temp_db):
        """Test database performance under concurrent access simulation"""
        import threading
        import queue
        
        results = queue.Queue()
        num_threads = 10
        operations_per_thread = 50
        
        def worker(thread_id):
            """Worker function for concurrent testing"""
            thread_results = []
            for i in range(operations_per_thread):
                start_time = time.time()
                
                # Mix of read and write operations
                if i % 3 == 0:
                    # Write operation
                    voice_file = VoiceFile(
                        file_id=f"concurrent_{thread_id}_{i}",
                        file_size=1024
                    )
                    temp_db.save_voice_file(voice_file)
                else:
                    # Read operation
                    temp_db.get_all_voice_files()
                
                operation_time = time.time() - start_time
                thread_results.append(operation_time)
            
            results.put((thread_id, thread_results))
        
        # Run concurrent operations
        threads = []
        overall_start = time.time()
        
        for thread_id in range(num_threads):
            thread = threading.Thread(target=worker, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        overall_time = time.time() - overall_start
        
        # Collect and analyze results
        all_operation_times = []
        while not results.empty():
            thread_id, thread_times = results.get()
            all_operation_times.extend(thread_times)
        
        # Performance assertions
        avg_operation_time = sum(all_operation_times) / len(all_operation_times)
        max_operation_time = max(all_operation_times)
        
        assert avg_operation_time < 0.1  # Average operation under 100ms
        assert max_operation_time < 0.5  # No single operation over 500ms
        assert overall_time < 30.0  # Complete test under 30 seconds
        
        print(f"\\nConcurrent access: {len(all_operation_times)} operations in {overall_time:.2f}s")
        print(f"Average operation time: {avg_operation_time*1000:.1f}ms")
        print(f"Max operation time: {max_operation_time*1000:.1f}ms")


class TestMemoryUsage:
    """Test memory usage patterns"""
    
    def test_memory_usage_bulk_processing(self):
        """Test memory usage during bulk processing simulation"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate processing many files
        voice_files = []
        for i in range(1000):
            voice_file = VoiceFile(
                file_id=f"memory_test_{i}",
                file_size=1024 * 100,  # 100KB each
                transcript=f"Long transcript content for memory testing " * 50,  # ~2KB transcript
                metadata={"test": "memory", "data": list(range(100))}  # Some structured data
            )
            voice_files.append(voice_file)
        
        # Check memory after object creation
        post_creation_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = post_creation_memory - initial_memory
        
        # Memory assertions
        assert memory_increase < 100  # Should not use more than 100MB for 1000 objects
        
        # Test memory cleanup
        del voice_files
        
        # Give garbage collector a chance
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\\nMemory usage test:")
        print(f"Initial: {initial_memory:.1f}MB")
        print(f"After creating 1000 objects: {post_creation_memory:.1f}MB (+{memory_increase:.1f}MB)")
        print(f"After cleanup: {final_memory:.1f}MB")


class TestProcessorPerformance:
    """Test VoiceProcessor performance characteristics"""
    
    @patch('src.voice_task_manager.integrations.drive.GoogleDriveClient')
    @patch('src.voice_task_manager.integrations.whisper.WhisperClient')
    @patch('src.voice_task_manager.integrations.notion.NotionClient')
    def test_processor_initialization_time(self, mock_notion, mock_whisper, mock_drive):
        """Test processor initialization performance"""
        with TemporaryDirectory() as temp_dir:
            start_time = time.time()
            processor = VoiceProcessor(project_root=Path(temp_dir))
            init_time = time.time() - start_time
            
            # Initialization should be fast
            assert init_time < 2.0  # Under 2 seconds
            
            print(f"\\nProcessor initialization: {init_time:.3f}s")
    
    @patch('src.voice_task_manager.integrations.drive.GoogleDriveClient')
    @patch('src.voice_task_manager.integrations.whisper.WhisperClient') 
    @patch('src.voice_task_manager.integrations.notion.NotionClient')
    def test_file_discovery_performance(self, mock_notion, mock_whisper, mock_drive):
        """Test file discovery performance with mocked API responses"""
        with TemporaryDirectory() as temp_dir:
            processor = VoiceProcessor(project_root=Path(temp_dir))
            
            # Mock drive client to return many files
            mock_files = []
            for i in range(100):
                mock_files.append({
                    'id': f'mock_file_{i}',
                    'name': f'voice_recording_{i}.m4a',
                    'size': str(1024 * (i + 1)),
                    'mimeType': 'audio/mp4',
                    'createdTime': '2025-01-01T12:00:00.000Z'
                })
            
            mock_drive.return_value.list_voice_files.return_value = mock_files
            
            start_time = time.time()
            discovered_files = processor.discover_voice_files()
            discovery_time = time.time() - start_time
            
            # Discovery should be efficient
            assert discovery_time < 5.0  # Under 5 seconds for 100 files
            assert len(discovered_files) == 100
            
            print(f"\\nFile discovery: {len(discovered_files)} files in {discovery_time:.3f}s")


class TestScalabilityLimits:
    """Test system behavior at scale limits"""
    
    def test_database_size_limits(self):
        """Test database performance with large record counts"""
        with TemporaryDirectory() as temp_dir:
            db = VoiceDatabase(Path(temp_dir))
            
            # Test with progressively larger datasets
            dataset_sizes = [100, 500, 1000, 2000]
            performance_data = []
            
            for size in dataset_sizes:
                # Clear database
                db.cleanup_old_records(days_old=0)  # Clear all records
                
                # Insert test data
                start_time = time.time()
                for i in range(size):
                    voice_file = VoiceFile(
                        file_id=f"scale_test_{i:05d}",
                        file_size=1024 * (i % 100 + 1),
                        transcript=f"Scalability test transcript {i}" if i % 2 == 0 else None
                    )
                    db.save_voice_file(voice_file)
                insert_time = time.time() - start_time
                
                # Test query performance
                query_start = time.time()
                all_files = db.get_all_voice_files()
                query_time = time.time() - query_start
                
                assert len(all_files) == size
                performance_data.append((size, insert_time, query_time))
                
                print(f"Dataset size {size}: Insert {insert_time:.3f}s, Query {query_time:.3f}s")
            
            # Verify performance scales reasonably
            # Query time should not increase dramatically
            first_query_time = performance_data[0][2]
            last_query_time = performance_data[-1][2]
            
            # Query time should not increase more than 10x for 20x data
            assert last_query_time < first_query_time * 10
            
            return performance_data


if __name__ == "__main__":
    # Run performance tests individually for development
    print("Running performance tests...")
    
    # Example: run database performance test
    pytest.main([__file__ + "::TestDatabasePerformance::test_bulk_insert_performance", "-v", "-s"])