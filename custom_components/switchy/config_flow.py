"""Config flow: add a Switchy panel by its device id (and host)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_DEVICE_ID, CONF_HOST, CONF_NAMES, CONF_TYPES, DOMAIN
from .protocol import SwitchyError, SwitchyPanel


class SwitchyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add one panel at a time."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "SwitchyOptionsFlow":
        return SwitchyOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            devid = user_input[CONF_DEVICE_ID].strip()
            host = user_input[CONF_HOST].strip()
            panel = SwitchyPanel(devid=devid, host=host)
            try:
                info = await panel.identify(async_get_clientsession(self.hass))
            except SwitchyError:
                errors["base"] = "cannot_connect"
            else:
                got = str(info.get("devid", ""))
                if got and got != devid:
                    errors["base"] = "wrong_device"
                else:
                    await self.async_set_unique_id(devid)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=f"Switchy {devid}", data={CONF_DEVICE_ID: devid, CONF_HOST: host})

        schema = vol.Schema({vol.Required(CONF_DEVICE_ID): str, vol.Required(CONF_HOST): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class SwitchyOptionsFlow(OptionsFlow):
    """Rename a panel's channels (L1, L2, ...) to friendly names."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            names = {k[5:]: v.strip() for k, v in user_input.items() if k.startswith("name_") and v.strip()}
            types = {k[5:]: v for k, v in user_input.items() if k.startswith("type_") and v == "fan"}
            return self.async_create_entry(title="", data={CONF_NAMES: names, CONF_TYPES: types})

        coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]
        names = self.config_entry.options.get(CONF_NAMES, {})
        types = self.config_entry.options.get(CONF_TYPES, {})
        channels = sorted(coordinator.data, key=lambda c: int(c[1:]))
        fields: dict[Any, Any] = {}
        for ch in channels:
            fields[vol.Optional(f"name_{ch}", default=names.get(ch, ""))] = str
            fields[vol.Optional(f"type_{ch}", default=types.get(ch, "switch"))] = vol.In(["switch", "fan"])
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))
