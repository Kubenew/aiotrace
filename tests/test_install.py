"""Tests for the install/uninstall mechanism."""

from __future__ import annotations

import asyncio

import pytest

from aiotrace import install, is_installed, uninstall


@pytest.mark.asyncio
async def test_install_and_uninstall():
    assert not is_installed()
    install()
    assert is_installed()
    uninstall()
    assert not is_installed()


@pytest.mark.asyncio
async def test_install_idempotent():
    install()
    assert is_installed()
    # Second call should be a no-op
    install()
    assert is_installed()
    uninstall()


@pytest.mark.asyncio
async def test_create_task_still_works_after_install():
    install()
    try:
        async def dummy():
            return 42

        result = await asyncio.create_task(dummy())
        assert result == 42
    finally:
        uninstall()
