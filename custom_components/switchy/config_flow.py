"""Config flow: add a Switchy panel by its device id (and host)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_DEVICE_ID, CONF_HOST, DOMAIN
from .protocol import SwitchyError, SwitchyPanel


class SwitchyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add one panel at a time."""

    VERSION = 1

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
