"""Config flow for Yasno Outages integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from . import DOMAIN, CONF_CITY, CONF_GROUP, CONF_SCAN_INTERVAL

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CITY): cv.string,
        vol.Required(CONF_GROUP): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=5): cv.positive_int,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yasno Outages."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check if entry already exists
            await self.async_set_unique_id(
                f"{user_input[CONF_CITY]}_{user_input[CONF_GROUP]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Yasno Outages {user_input[CONF_CITY].title()} Group {user_input[CONF_GROUP]}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )