from prometheus_client import Counter, Histogram, Gauge
import time


class MetricsManager:
    """
    Manages Prometheus metrics for the translation service.

    Provides a centralized way to track and expose application metrics including
    job statistics, processing times, connection counts, and DLQ status using
    Prometheus client types (Counter, Histogram, Gauge).

    Example:
        metrics = MetricsManager()
        metrics.track_job_created()

        with metrics.track_processing_time():
            process_translation()

    Attributes:
        job_created: Counter for total jobs created
        job_completed: Counter for successfully completed jobs
        job_errors: Counter for failed jobs
        processing_time: Histogram for translation processing duration
        active_connections: Gauge for current WebSocket connection count
        dlq_size: Gauge for current size of Dead Letter Queue
    """

    def __init__(self):
        """
        Initialize Prometheus metrics collectors.

        Creates Counter, Histogram, and Gauge instances with appropriate
        names and descriptions for monitoring translation service behavior.
        """
        # Counters
        self.job_created = Counter(
            "translation_job_created_total", "Total jobs created"
        )
        self.job_completed = Counter(
            "translation_job_completed_total", "Total jobs completed"
        )
        self.job_errors = Counter("translation_job_errors_total", "Total job errors")

        # Histograms
        self.processing_time = Histogram(
            "translation_processing_seconds", "Time spent processing translations"
        )

        # Gauges
        self.active_connections = Gauge(
            "translation_active_connections", "Number of active WebSocket connections"
        )
        self.dlq_size = Gauge("translation_dlq_size", "Number of jobs in DLQ")

    def track_job_created(self):
        """
        Increment the job creation counter.

        Should be called when a new translation job is created.
        """
        self.job_created.inc()

    def track_job_completed(self):
        """
        Increment the job completion counter.

        Should be called when a translation job completes successfully.
        """
        self.job_completed.inc()

    def track_job_error(self):
        """
        Increment the job error counter.

        Should be called when a translation job fails with an error.
        """
        self.job_errors.inc()

    def track_processing_time(self):
        """
        Create a context manager for tracking job processing duration.

        Returns:
            A context manager that records the execution time of the block
            to the processing_time histogram.

        Example:
            with metrics.track_processing_time():
                # Process translation
                translate_video()
        """
        return self.processing_time.time()

    def set_active_connections(self, count: int):
        """
        Update the active WebSocket connections gauge.

        Args:
            count: Current number of active WebSocket connections
        """
        self.active_connections.set(count)

    def set_dlq_size(self, size: int):
        """
        Update the Dead Letter Queue size gauge.

        Args:
            size: Current number of jobs in the DLQ
        """
        self.dlq_size.set(size)
