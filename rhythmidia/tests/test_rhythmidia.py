"""
Unit and regression test for the rhythmidia package.
"""

# Import package, test suite, and other packages as needed
import sys

import pytest

import rhythmidia


def test_rhythmidia_imported():
    """Sample test, will always pass so long as import statement worked."""
    assert "rhythmidia" in sys.modules
