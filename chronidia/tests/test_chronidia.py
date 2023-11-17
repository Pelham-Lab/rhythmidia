"""
Unit and regression test for the chronidia package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest

import chronidia


def test_chronidia_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "chronidia" in sys.modules
