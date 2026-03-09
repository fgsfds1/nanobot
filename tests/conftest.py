"""Shared test fixtures."""

import pytest


@pytest.fixture(autouse=True)
def reset_loader_state():
    """Reset loader global state before and after each test."""
    from nanobot.config import loader

    # Save original state
    original_config_path = loader._current_config_path
    original_data_dir = loader._current_data_dir

    # Reset to None
    loader._current_config_path = None
    loader._current_data_dir = None

    yield

    # Restore original state
    loader._current_config_path = original_config_path
    loader._current_data_dir = original_data_dir
