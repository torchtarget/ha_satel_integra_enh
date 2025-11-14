"""Satel Integra base entity."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from satel_integra import AsyncSatel

from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import area_registry as ar, device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_AREA,
    DOMAIN,
    SUBENTRY_TYPE_OUTPUT,
    SUBENTRY_TYPE_PARTITION,
    SUBENTRY_TYPE_SWITCHABLE_OUTPUT,
    SUBENTRY_TYPE_ZONE,
)

_LOGGER = logging.getLogger(__name__)

SubentryTypeToEntityType: dict[str, str] = {
    SUBENTRY_TYPE_PARTITION: "alarm_panel",
    SUBENTRY_TYPE_SWITCHABLE_OUTPUT: "switch",
    SUBENTRY_TYPE_ZONE: "zones",
    SUBENTRY_TYPE_OUTPUT: "outputs",
}


class SatelIntegraEntity(Entity):
    """Defines a base Satel Integra entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        controller: AsyncSatel,
        config_entry_id: str,
        subentry: ConfigSubentry,
        device_number: int,
    ) -> None:
        """Initialize the Satel Integra entity."""

        self._satel = controller
        self._device_number = device_number
        self._subentry = subentry  # Store for area assignment later

        entity_type = SubentryTypeToEntityType[subentry.subentry_type]

        if TYPE_CHECKING:
            assert entity_type is not None

        self._attr_unique_id = f"{config_entry_id}_{entity_type}_{device_number}"

        # Build device info with optional area assignment
        device_info_params: dict = {
            "name": subentry.data[CONF_NAME],
            "identifiers": {(DOMAIN, self._attr_unique_id)},
        }

        # If area is specified in config, add suggested_area parameter
        if area_name := subentry.data.get(CONF_AREA):
            device_info_params["suggested_area"] = area_name
            _LOGGER.info(
                "🔵 SATEL DEVICE INIT: Creating device '%s' (zone %s) with suggested_area='%s'",
                subentry.data[CONF_NAME],
                device_number,
                area_name,
            )
        else:
            _LOGGER.debug(
                "SATEL DEVICE INIT: Creating device '%s' (zone %s) WITHOUT area",
                subentry.data[CONF_NAME],
                device_number,
            )

        _LOGGER.info(
            "🟡 SATEL DEVICE INFO: device_info_params = %s",
            device_info_params,
        )

        self._attr_device_info = DeviceInfo(**device_info_params)

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant - assign device to area."""
        await super().async_added_to_hass()

        # Check if area is specified in config
        area_name = self._subentry.data.get(CONF_AREA)
        if not area_name:
            _LOGGER.debug(
                "No area specified for device '%s' (zone %s)",
                self._subentry.data[CONF_NAME],
                self._device_number,
            )
            return

        _LOGGER.info(
            "🔵 SATEL AREA ASSIGNMENT: Processing device '%s' (zone %s) -> area '%s'",
            self._subentry.data[CONF_NAME],
            self._device_number,
            area_name,
        )

        # Get the area registry and find/create the area
        area_reg = ar.async_get(self.hass)

        # Try to find area by ID first (e.g., "technical_room")
        area_entry = area_reg.async_get_area(area_name)

        if area_entry:
            _LOGGER.info(
                "🟢 SATEL AREA: Found existing area by ID '%s' (name: '%s')",
                area_name,
                area_entry.name,
            )
        else:
            # Try to find by name (e.g., "Technical Room")
            area_entry = area_reg.async_get_area_by_name(area_name)

            if area_entry:
                _LOGGER.info(
                    "🟢 SATEL AREA: Found existing area by NAME '%s' (ID: %s)",
                    area_name,
                    area_entry.id,
                )
            else:
                # Create new area if it doesn't exist
                area_entry = area_reg.async_create(area_name)
                _LOGGER.info(
                    "🆕 SATEL AREA: Created new area '%s' (ID: %s)",
                    area_name,
                    area_entry.id,
                )

        # Get the device registry and find our device
        device_reg = dr.async_get(self.hass)
        device_entry = device_reg.async_get_device(
            identifiers={(DOMAIN, self._attr_unique_id)}
        )

        if not device_entry:
            _LOGGER.error(
                "🔴 SATEL AREA ERROR: Device not found in registry for '%s' (unique_id: %s)",
                self._subentry.data[CONF_NAME],
                self._attr_unique_id,
            )
            return

        _LOGGER.info(
            "🟡 SATEL AREA: Found device '%s' (device_id: %s, current_area: %s)",
            device_entry.name,
            device_entry.id,
            device_entry.area_id,
        )

        # Update the device's area
        device_reg.async_update_device(device_entry.id, area_id=area_entry.id)

        _LOGGER.info(
            "✅ SATEL AREA SUCCESS: Device '%s' assigned to area '%s' (area_id: %s)",
            self._subentry.data[CONF_NAME],
            area_name,
            area_entry.id,
        )
