"""A switch entity per panel channel."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAMES, CONF_TYPES, DOMAIN
from .coordinator import SwitchyCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """One switch entity per channel the panel reports."""
    coordinator: SwitchyCoordinator = hass.data[DOMAIN][entry.entry_id]
    names = entry.options.get(CONF_NAMES, {})
    types = entry.options.get(CONF_TYPES, {})
    channels = [ch for ch in sorted(coordinator.data, key=lambda c: int(c[1:])) if types.get(ch) != "fan"]
    async_add_entities(SwitchyChannel(coordinator, ch, names.get(ch)) for ch in channels)


class SwitchyChannel(CoordinatorEntity[SwitchyCoordinator], SwitchEntity):
    """One channel (relay) on a Switchy panel."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SwitchyCoordinator, channel: str, name: str | None = None) -> None:
        super().__init__(coordinator)
        self._channel = channel
        devid = coordinator.panel.devid
        self._attr_unique_id = f"{devid}_{channel}"
        self._attr_name = name or channel
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, devid)}, name=f"Switchy {devid}", manufacturer="Switchy", model="Touch panel",
        )

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self._channel)
        return None if value is None else value != 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set(self._channel, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set(self._channel, 0)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
