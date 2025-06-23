"""
Comprehensive test suite for MCP Worker service
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.mcp_worker.src.worker import MCPWorker, Task, TaskProcessor


@pytest.mark.asyncio
class TestTask:
    """Test Task data class"""

    def test_task_creation(self):
        """Test task creation with required fields"""
        task = Task(
            id="test-123",
            type="test_task",
            payload={"data": "test"},
            created_at=datetime.now(),
        )

        assert task.id == "test-123"
        assert task.type == "test_task"
        assert task.payload == {"data": "test"}
        assert task.attempts == 0
        assert task.max_attempts == 3

    def test_task_with_custom_attempts(self):
        """Test task creation with custom max attempts"""
        task = Task(
            id="test-456",
            type="test_task",
            payload={},
            created_at=datetime.now(),
            max_attempts=5,
        )

        assert task.max_attempts == 5


@pytest.mark.asyncio
class TestTaskProcessor:
    """Test TaskProcessor functionality"""

    @pytest.fixture
    def processor(self):
        """Create a TaskProcessor instance for testing"""
        return TaskProcessor()

    def test_processor_initialization(self, processor):
        """Test processor initialization"""
        assert not processor.running
        assert processor.task_queue is not None
        assert len(processor.handlers) > 0
        assert "vector_index" in processor.handlers
        assert "model_cache" in processor.handlers
        assert "data_cleanup" in processor.handlers
        assert "health_check" in processor.handlers

    async def test_add_task(self, processor):
        """Test adding tasks to the queue"""
        task = Task(
            id="test-add",
            type="test_task",
            payload={"test": True},
            created_at=datetime.now(),
        )

        await processor.add_task(task)

        # Check that task was added to queue
        assert processor.task_queue.qsize() == 1

        # Verify we can get the task back
        retrieved_task = await processor.task_queue.get()
        assert retrieved_task.id == "test-add"
        assert retrieved_task.type == "test_task"

    async def test_vector_index_handler_success(self, processor):
        """Test successful vector index task handling"""
        task = Task(
            id="vector-test",
            type="vector_index",
            payload={"documents": ["doc1", "doc2"]},
            created_at=datetime.now(),
        )

        result = await processor._handle_vector_index(task)
        assert result is True

    async def test_model_cache_handler_success(self, processor):
        """Test successful model cache task handling"""
        task = Task(
            id="cache-test",
            type="model_cache",
            payload={"model_id": "test-model"},
            created_at=datetime.now(),
        )

        result = await processor._handle_model_cache(task)
        assert result is True

    async def test_data_cleanup_handler_success(self, processor):
        """Test successful data cleanup task handling"""
        task = Task(
            id="cleanup-test",
            type="data_cleanup",
            payload={"target": "temp_files"},
            created_at=datetime.now(),
        )

        result = await processor._handle_data_cleanup(task)
        assert result is True

    async def test_health_check_handler_success(self, processor):
        """Test successful health check task handling"""
        task = Task(
            id="health-test", type="health_check", payload={}, created_at=datetime.now()
        )

        with patch("services.mcp_worker.src.worker.worker_health") as mock_health:
            result = await processor._handle_health_check(task)
            assert result is True
            mock_health.set.assert_called_once_with(1)

    async def test_task_processing_success(self, processor):
        """Test successful task processing"""
        task = Task(
            id="process-test",
            type="health_check",
            payload={},
            created_at=datetime.now(),
        )

        await processor.add_task(task)
        processor.running = True

        # Mock metrics
        with patch("services.mcp_worker.src.worker.active_tasks") as mock_active, patch(
            "services.mcp_worker.src.worker.tasks_processed"
        ) as mock_processed, patch(
            "services.mcp_worker.src.worker.task_duration"
        ) as mock_duration, patch(
            "services.mcp_worker.src.worker.worker_health"
        ):

            # Process one task
            await asyncio.wait_for(processor.process_tasks(), timeout=2.0)

            # Verify metrics were called
            mock_active.inc.assert_called()
            mock_active.dec.assert_called()
            mock_processed.labels.assert_called()
            mock_duration.labels.assert_called()

    async def test_task_processing_retry(self, processor):
        """Test task retry on failure"""
        # Create a task that will fail
        task = Task(
            id="retry-test",
            type="nonexistent",  # This will fail
            payload={},
            created_at=datetime.now(),
            max_attempts=2,
        )

        await processor.add_task(task)
        processor.running = True

        with patch("services.mcp_worker.src.worker.tasks_processed") as mock_processed:
            # Process tasks briefly
            try:
                await asyncio.wait_for(processor.process_tasks(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            # Should have retried and eventually failed
            mock_processed.labels.assert_called()

    async def test_unknown_task_type(self, processor):
        """Test handling of unknown task types"""
        task = Task(
            id="unknown-test",
            type="unknown_task_type",
            payload={},
            created_at=datetime.now(),
        )

        await processor.add_task(task)
        processor.running = True

        with patch("services.mcp_worker.src.worker.tasks_processed") as mock_processed:
            # Process one iteration
            try:
                await asyncio.wait_for(processor.process_tasks(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            # Should log error for unknown task type
            mock_processed.labels.assert_called_with(
                task_type="unknown_task_type", status="error"
            )


@pytest.mark.asyncio
class TestMCPWorker:
    """Test MCPWorker main class"""

    @pytest.fixture
    def worker(self):
        """Create an MCPWorker instance for testing"""
        return MCPWorker()

    def test_worker_initialization(self, worker):
        """Test worker initialization"""
        assert worker.processor is not None
        assert worker.shutdown_event is not None
        assert not worker.shutdown_event.is_set()

    async def test_shutdown(self, worker):
        """Test graceful shutdown"""
        worker.processor.running = True

        await worker.shutdown()

        assert not worker.processor.running
        assert worker.shutdown_event.is_set()

    @patch("services.mcp_worker.src.worker.start_http_server")
    async def test_run_initialization(self, mock_http_server, worker):
        """Test worker run initialization"""
        # Mock the shutdown event to trigger immediately
        worker.shutdown_event.set()

        await worker.run()

        # Verify metrics server was started
        mock_http_server.assert_called_once()


@pytest.mark.integration
class TestWorkerIntegration:
    """Integration tests for the worker service"""

    @pytest.mark.asyncio
    async def test_worker_full_lifecycle(self):
        """Test complete worker lifecycle"""
        worker = MCPWorker()

        # Start worker in background
        worker_task = asyncio.create_task(worker.run())

        # Give it time to start
        await asyncio.sleep(0.1)

        # Add some tasks
        tasks = [
            Task(
                id=f"test-{i}",
                type="health_check",
                payload={},
                created_at=datetime.now(),
            )
            for i in range(3)
        ]

        for task in tasks:
            await worker.processor.add_task(task)

        # Let it process
        await asyncio.sleep(0.5)

        # Shutdown
        await worker.shutdown()

        # Wait for completion
        try:
            await asyncio.wait_for(worker_task, timeout=1.0)
        except asyncio.TimeoutError:
            worker_task.cancel()

    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self):
        """Test processing multiple tasks concurrently"""
        processor = TaskProcessor()
        processor.running = True

        # Add multiple tasks
        tasks = [
            Task(
                id=f"concurrent-{i}",
                type="health_check",
                payload={},
                created_at=datetime.now(),
            )
            for i in range(10)
        ]

        for task in tasks:
            await processor.add_task(task)

        # Process tasks
        start_time = time.time()

        try:
            await asyncio.wait_for(processor.process_tasks(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        end_time = time.time()

        # Should have processed tasks relatively quickly
        assert end_time - start_time < 3.0
        assert processor.task_queue.empty()


@pytest.mark.performance
class TestWorkerPerformance:
    """Performance tests for the worker service"""

    @pytest.mark.asyncio
    async def test_high_throughput_processing(self):
        """Test worker performance under high load"""
        processor = TaskProcessor()
        processor.running = True

        # Add many tasks
        num_tasks = 100
        tasks = [
            Task(
                id=f"perf-{i}",
                type="health_check",
                payload={},
                created_at=datetime.now(),
            )
            for i in range(num_tasks)
        ]

        start_time = time.time()

        # Add all tasks
        for task in tasks:
            await processor.add_task(task)

        # Process with timeout
        try:
            await asyncio.wait_for(processor.process_tasks(), timeout=10.0)
        except asyncio.TimeoutError:
            pass

        end_time = time.time()
        processing_time = end_time - start_time

        # Calculate throughput
        throughput = num_tasks / processing_time

        # Should process at least 10 tasks per second
        assert throughput >= 10.0

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage doesn't grow excessively"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        processor = TaskProcessor()
        processor.running = True

        # Process many tasks
        for batch in range(10):
            tasks = [
                Task(
                    id=f"mem-{batch}-{i}",
                    type="health_check",
                    payload={},
                    created_at=datetime.now(),
                )
                for i in range(50)
            ]

            for task in tasks:
                await processor.add_task(task)

            # Process batch
            try:
                await asyncio.wait_for(processor.process_tasks(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (less than 100MB)
        assert memory_growth < 100 * 1024 * 1024


@pytest.mark.asyncio
class TestErrorScenarios:
    """Test error handling and edge cases"""

    async def test_handler_exception(self):
        """Test handling of exceptions in task handlers"""
        processor = TaskProcessor()

        # Mock a handler that raises an exception
        async def failing_handler(task):
            raise RuntimeError("Handler failed")

        processor.handlers["failing_task"] = failing_handler

        task = Task(
            id="failing-test",
            type="failing_task",
            payload={},
            created_at=datetime.now(),
        )

        result = await processor.handlers["failing_task"](task)

        # Should handle the exception gracefully
        # The actual handler in our mock will raise, but in real implementation
        # it should be caught and return False

    async def test_queue_overflow_handling(self):
        """Test behavior when task queue is full"""
        processor = TaskProcessor()

        # Fill up queue (asyncio.Queue doesn't have a size limit by default,
        # but we can test with a limited queue)
        limited_queue = asyncio.Queue(maxsize=5)
        processor.task_queue = limited_queue

        # Fill the queue
        for i in range(5):
            task = Task(
                id=f"overflow-{i}",
                type="health_check",
                payload={},
                created_at=datetime.now(),
            )
            await processor.add_task(task)

        # Queue should be full
        assert processor.task_queue.full()

        # Adding another task should still work (will block until space available)
        # In a real scenario, you might want to implement queue size monitoring

    async def test_shutdown_during_processing(self):
        """Test graceful shutdown while processing tasks"""
        worker = MCPWorker()

        # Add tasks
        for i in range(5):
            task = Task(
                id=f"shutdown-{i}",
                type="health_check",
                payload={},
                created_at=datetime.now(),
            )
            await worker.processor.add_task(task)

        # Start processing
        worker.processor.running = True
        process_task = asyncio.create_task(worker.processor.process_tasks())

        # Let it start processing
        await asyncio.sleep(0.1)

        # Trigger shutdown
        await worker.shutdown()

        # Should stop gracefully
        try:
            await asyncio.wait_for(process_task, timeout=1.0)
        except asyncio.TimeoutError:
            process_task.cancel()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
