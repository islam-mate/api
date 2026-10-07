"""
Shared pytest fixtures for the Islam Mate API test suite.
"""
import pytest
from kernel.rate_limiter import _request_counts


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """
    Clear the in-memory rate-limiter counter before (and after) every test.

    The rate limiter uses a shared defaultdict keyed by client IP.
    During test runs all requests originate from the same synthetic IP
    ('testclient'), so the 60-req/minute limit is quickly exhausted and
    subsequent tests receive HTTP 429 instead of the expected response.
    Resetting the counter here keeps each test fully independent.
    """
    _request_counts.clear()
    yield
    _request_counts.clear()