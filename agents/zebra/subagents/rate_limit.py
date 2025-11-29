"""
Rate Limit Configuration for Zebra Agents

This module provides a shared rate limit configuration that can be imported
by all agents to handle 429 (RESOURCE_EXHAUSTED) errors gracefully.
"""

from google.genai import types


# Default retry configuration for handling rate limits
# - initial_delay: Wait 30 seconds before first retry
# - attempts: Retry up to 5 times before giving up
DEFAULT_RETRY_CONFIG = types.GenerateContentConfig(
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            initial_delay=30,  # Wait 30 seconds before first retry
            attempts=5,        # Retry up to 5 times
        ),
    ),
)


def get_retry_config(initial_delay: int = 30, attempts: int = 5) -> types.GenerateContentConfig:
    """
    Get a custom retry configuration.
    
    Args:
        initial_delay: Seconds to wait before first retry (default: 30)
        attempts: Maximum number of retry attempts (default: 5)
    
    Returns:
        GenerateContentConfig with retry options configured
    """
    return types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                initial_delay=initial_delay,
                attempts=attempts,
            ),
        ),
    )
