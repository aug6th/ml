"""
Core logging functionality.

This module provides consistent logging configuration across the Mercury platform.
"""

import logging
import time
from datetime import datetime, timedelta

from ml.logging.config import configure_logging

# Configure root logger on import
configure_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with consistent formatting.

    Args:
        name: The name of the logger

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)


class CloudWatchLogger:
    """Cloud Watch logger class to read and write logs to Cloud Watch
    # Usage
    cloudwatch1 = CloudWatchLogger()
    cloudwatch2 = CloudWatchLogger()

    print(cloudwatch1 is cloudwatch2)  # True
    print(cloudwatch1.client)  # Boto3 CloudWatch Logs client
    print(cloudwatch2.client)  # Boto3 CloudWatch Logs client
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        import boto3  # putting import here because not all projects have boto3 package.

        if cls._instance is None:
            cls._instance = super(CloudWatchLogger, cls).__new__(cls)
            cls._instance.client = boto3.client("logs", *args, **kwargs)
        return cls._instance

    @property
    def log_group_name(self):
        return self._log_group_name

    @log_group_name.setter
    def log_group_name(self, log_group_name: str):
        self._log_group_name = log_group_name

    @property
    def log_stream_name(self):
        return self._log_stream_name

    @log_stream_name.setter
    def log_stream_name(self, log_stream_name: str):
        self._log_stream_name = log_stream_name

    def write(self, message: str):
        """Write log to Cloud Watch

        Args:
            message (str): Log message
        """

        # Create log group if it doesn't exist
        try:
            self.client.create_log_group(logGroupName=self._log_group_name)
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

        # Create log stream if it doesn't exist
        try:
            self.client.create_log_stream(logGroupName=self._log_group_name, logStreamName=self._log_stream_name)
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass

        # Prepare log event
        log_event = {
            "timestamp": int(time.time() * 1000),  # Current time in milliseconds
            "message": message,
        }

        # Get the next sequence token
        response = self.client.describe_log_streams(
            logGroupName=self._log_group_name, logStreamNamePrefix=self._log_stream_name
        )
        log_streams = response["logStreams"]
        if log_streams:
            next_sequence_token = log_streams[0].get("uploadSequenceToken")
        else:
            next_sequence_token = None

        # Send log event
        kwargs = {
            "logGroupName": self._log_group_name,
            "logStreamName": self._log_stream_name,
            "logEvents": [log_event],
        }

        if next_sequence_token:
            kwargs["sequenceToken"] = next_sequence_token

        return self.client.put_log_events(**kwargs)

    def read(self, query: str, start_time: datetime = None, end_time: datetime = None):
        """Read logs from Cloud Watch

        Example query:

            fields @timestamp, @message
            | filter @logStream = "workflow"
            | filter @message like /session_id=asdf883.*/
            | sort @timestamp desc
            | limit 20

        Args:
            query (str): Query to filter logs
            start_time (datetime): Start time
            end_time (datetime): End time

        Returns:
            Pandas dataframe: Dataframe with logs
        """
        import awswrangler as wr  # putting import here because not all projects have awswrangler package.

        if not start_time or not end_time:
            # Define the time range for the last 30 minutes
            start_time = datetime.now() - timedelta(minutes=30)
            end_time = datetime.now()

        # Read logs from CloudWatch
        logs = wr.cloudwatch.read_logs(
            query=query, log_group_names=[self._log_group_name], start_time=start_time, end_time=end_time
        )
        return logs

