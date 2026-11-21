"""Polling coordinator: one panel's channel states."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .protocol import SwitchyError, SwitchyPanel

_LOGGER = logging.getLogger(__name__)


class SwitchyCoordinator(DataUpdateCoordinator[dict[str, int]]):
    """Keeps one panel's {channel: value} fresh."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, panel: SwitchyPanel) -> None:
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN} {panel.devid}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.panel = panel
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, int]:
        try:
            return await self.panel.status(self._session)
        except SwitchyError as err:
            raise UpdateFailed(str(err)) from err

    async def async_set(self, channel: str, value: int) -> None:
        """Set a channel and update the cached state."""
        try:
            data = await self.panel.set_channel(self._session, channel, value)
        except SwitchyError as err:
            raise UpdateFailed(str(err)) from err
        self.async_set_updated_data(data)
