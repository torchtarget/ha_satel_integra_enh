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

        # Build device info without suggested_area to prevent auto-creation of areas
        # Area assignment is handled in async_added_to_hass where we validate the area exists
        self._attr_device_info = DeviceInfo(
            name=subentry.data[CONF_NAME],
            identifiers={(DOMAIN, self._attr_unique_id)},
        )

    async def async_added_to_hass(self) -> None:
        """Handle entity added to Home Assistant - assign device to area."""
        await super().async_added_to_hass()

        # Check if area is specified in config
        area_name = self._subentry.data.get(CONF_AREA)
        if not area_name:
            return

        # Get the area registry and lookup the area
        area_reg = ar.async_get(self.hass)

        # Try to find area by ID first (e.g., "technical_room")
        area_entry = area_reg.async_get_area(area_name)

        if not area_entry:
            # Try to find by name if ID lookup failed (e.g., "Technical Room")
            area_entry = area_reg.async_get_area_by_name(area_name)

        if not area_entry:
            # Area not found - skip assignment and warn user
            _LOGGER.warning(
                "Area '%s' not found for device '%s'. Device will not be assigned to an area. "
                "Check that the area exists in Home Assistant and matches the value in satel.yaml",
                area_name,
                self._subentry.data[CONF_NAME],
            )
            return

        # Get the device from registry
        device_reg = dr.async_get(self.hass)
        device_entry = device_reg.async_get_device(
            identifiers={(DOMAIN, self._attr_unique_id)}
        )

        if not device_entry:
            _LOGGER.error(
                "Device not found in registry for '%s' (unique_id: %s)",
                self._subentry.data[CONF_NAME],
                self._attr_unique_id,
            )
            return

        # Assign device to area
        device_reg.async_update_device(device_entry.id, area_id=area_entry.id)

        _LOGGER.debug(
            "Assigned device '%s' to area '%s'",
            self._subentry.data[CONF_NAME],
            area_entry.name,
        )
