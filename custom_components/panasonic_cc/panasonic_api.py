"""Helpers for Panasonic Comfort Cloud API quirks."""

from __future__ import annotations

from datetime import date

from aio_panasonic_comfort_cloud import ApiClient

from .const import PANASONIC_CLOUD_WORKING_APP_VERSION


async def prepare_api_client(api: ApiClient) -> None:
    """Load settings and pin the Panasonic app version that currently works."""
    await api._settings.is_ready()
    # Panasonic currently rejects newer advertised app versions with API error 4103.
    api._settings._version = PANASONIC_CLOUD_WORKING_APP_VERSION
    api._settings._versionDate = date.today()
