"""
Rate Limit Configuration for Cross Agents

This module provides a shared rate limit configuration that can be imported
by all agents to handle 429 (RESOURCE_EXHAUSTED) errors gracefully.
"""

from google.genai import types


# Default retry configuration for handling rate limits
DEFAULT_RETRY_CONFIG = types.GenerateContentConfig(
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            initial_delay=30,
            attempts=5,
        ),
    ),
)
