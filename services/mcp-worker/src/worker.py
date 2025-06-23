"""MCP Worker Service - Background task processor for MCP operations"""

import asyncio
import os
import signal
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import structlog
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Metrics
tasks_processed = Counter(
    "mcp_worker_tasks_processed_total", "Total tasks processed", ["task_type", "status"]
)
task_duration = Histogram(
    "mcp_worker_task_duration_seconds", "Task processing duration", ["task_type"]
)
active_tasks = Gauge("mcp_worker_active_tasks", "Number of active tasks")
worker_health = Gauge(
    "mcp_worker_health", "Worker health status (1=healthy, 0=unhealthy)"
)


@dataclass
class Task:
    """Represents a background task"""

    id: str
    type: str
    payload: Dict[str, Any]
    created_at: datetime
    attempts: int = 0
    max_attempts: int = 3


class TaskProcessor:
    """Processes background tasks"""

    def __init__(self):
        self.running = False
        self.task_queue = asyncio.Queue()
        self.handlers = {}
        self.register_handlers()

    def register_handlers(self):
        """Register task handlers"""
        self.handlers = {
            "vector_index": self._handle_vector_index,
            "model_cache": self._handle_model_cache,
            "data_cleanup": self._handle_data_cleanup,
            "health_check": self._handle_health_check,
        }

    async def _handle_vector_index(self, task: Task) -> bool:
        """Handle vector indexing tasks"""
        try:
            logger.info(
                "Processing vector index task", task_id=task.id, payload=task.payload
            )

            # Simulate vector indexing work
            await asyncio.sleep(1.0)  # Replace with actual vector indexing logic

            logger.info("Vector index task completed", task_id=task.id)
            return True

        except Exception as e:
            logger.error("Vector index task failed", task_id=task.id, error=str(e))
            return False

    async def _handle_model_cache(self, task: Task) -> bool:
        """Handle model caching tasks"""
        try:
            logger.info(
                "Processing model cache task", task_id=task.id, payload=task.payload
            )

            # Simulate model caching work
            await asyncio.sleep(0.5)  # Replace with actual model caching logic

            logger.info("Model cache task completed", task_id=task.id)
            return True

        except Exception as e:
            logger.error("Model cache task failed", task_id=task.id, error=str(e))
            return False

    async def _handle_data_cleanup(self, task: Task) -> bool:
        """Handle data cleanup tasks"""
        try:
            logger.info(
                "Processing data cleanup task", task_id=task.id, payload=task.payload
            )

            # Simulate cleanup work
            await asyncio.sleep(0.2)  # Replace with actual cleanup logic

            logger.info("Data cleanup task completed", task_id=task.id)
            return True

        except Exception as e:
            logger.error("Data cleanup task failed", task_id=task.id, error=str(e))
            return False

    async def _handle_health_check(self, task: Task) -> bool:
        """Handle health check tasks"""
        try:
            logger.info("Processing health check task", task_id=task.id)

            # Update worker health metric
            worker_health.set(1)

            logger.info("Health check task completed", task_id=task.id)
            return True

        except Exception as e:
            logger.error("Health check task failed", task_id=task.id, error=str(e))
            worker_health.set(0)
            return False

    async def add_task(self, task: Task):
        """Add a task to the queue"""
        await self.task_queue.put(task)
        logger.info("Task added to queue", task_id=task.id, task_type=task.type)

    async def process_tasks(self):
        """Main task processing loop"""
        logger.info("Starting task processor")

        while self.running:
            try:
                # Wait for a task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                active_tasks.inc()
                start_time = asyncio.get_event_loop().time()

                try:
                    # Get handler for task type
                    handler = self.handlers.get(task.type)
                    if not handler:
                        logger.error(
                            "No handler for task type",
                            task_type=task.type,
                            task_id=task.id,
                        )
                        tasks_processed.labels(
                            task_type=task.type, status="error"
                        ).inc()
                        continue

                    # Process the task
                    task.attempts += 1
                    success = await handler(task)

                    # Record metrics
                    duration = asyncio.get_event_loop().time() - start_time
                    task_duration.labels(task_type=task.type).observe(duration)

                    if success:
                        tasks_processed.labels(
                            task_type=task.type, status="success"
                        ).inc()
                        logger.info(
                            "Task processed successfully",
                            task_id=task.id,
                            task_type=task.type,
                            duration=duration,
                        )
                    else:
                        # Retry if not exceeded max attempts
                        if task.attempts < task.max_attempts:
                            logger.warning(
                                "Task failed, retrying",
                                task_id=task.id,
                                task_type=task.type,
                                attempts=task.attempts,
                            )
                            await self.task_queue.put(task)
                        else:
                            logger.error(
                                "Task failed after max attempts",
                                task_id=task.id,
                                task_type=task.type,
                                attempts=task.attempts,
                            )
                            tasks_processed.labels(
                                task_type=task.type, status="failed"
                            ).inc()

                except Exception as e:
                    logger.error(
                        "Unexpected error processing task",
                        task_id=task.id,
                        error=str(e),
                    )
                    tasks_processed.labels(task_type=task.type, status="error").inc()

                finally:
                    active_tasks.dec()

            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error("Error in task processing loop", error=str(e))
                await asyncio.sleep(1.0)

        logger.info("Task processor stopped")


class MCPWorker:
    """Main MCP Worker service"""

    def __init__(self):
        self.processor = TaskProcessor()
        self.shutdown_event = asyncio.Event()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Initiating graceful shutdown")
        self.processor.running = False
        self.shutdown_event.set()

    async def run(self):
        """Main run loop"""
        logger.info("Starting MCP Worker", version="1.0.0")

        # Start metrics server
        metrics_port = int(os.getenv("METRICS_PORT", "9090"))
        start_http_server(metrics_port)
        logger.info("Metrics server started", port=metrics_port)

        # Setup signal handlers
        self.setup_signal_handlers()

        # Start task processor
        self.processor.running = True

        # Add initial health check task
        health_task = Task(
            id="initial-health-check",
            type="health_check",
            payload={},
            created_at=datetime.now(),
        )
        await self.processor.add_task(health_task)

        # Create task processor coroutine
        processor_task = asyncio.create_task(self.processor.process_tasks())

        # Create periodic health check task
        async def periodic_health_check():
            while self.processor.running:
                await asyncio.sleep(30)  # Health check every 30 seconds
                if self.processor.running:
                    health_task = Task(
                        id=f"health-check-{datetime.now().isoformat()}",
                        type="health_check",
                        payload={},
                        created_at=datetime.now(),
                    )
                    await self.processor.add_task(health_task)

        health_check_task = asyncio.create_task(periodic_health_check())

        try:
            # Wait for shutdown signal
            await self.shutdown_event.wait()
        finally:
            # Cancel tasks
            processor_task.cancel()
            health_check_task.cancel()

            try:
                await processor_task
            except asyncio.CancelledError:
                pass

            try:
                await health_check_task
            except asyncio.CancelledError:
                pass

            logger.info("MCP Worker shutdown complete")


async def main():
    """Main entry point"""
    worker = MCPWorker()
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error", error=str(e))
        sys.exit(1)
