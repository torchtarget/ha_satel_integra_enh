"""Support for Satel Integra zone states- represented as binary sensors."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from satel_integra_enh import AsyncSatel

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_OUTPUT_NUMBER,
    CONF_ZONE_NUMBER,
    CONF_ZONE_TYPE,
    SIGNAL_OUTPUTS_UPDATED,
    SIGNAL_ZONES_UPDATED,
    SUBENTRY_TYPE_OUTPUT,
    SUBENTRY_TYPE_ZONE,
    SatelConfigEntry,
)
from .entity import SatelIntegraEntity

_LOGGER = logging.getLogger(__name__)

# Temperature polling interval - 5 minutes to avoid overwhelming the connection
# Temperature doesn't change rapidly in smoke detectors, so slow polling is acceptable
TEMPERATURE_SCAN_INTERVAL = timedelta(minutes=5)

# Delay between sequential temperature requests (10 seconds)
TEMPERATURE_REQUEST_DELAY = 10


async def _temperature_polling_task(
    hass: HomeAssistant,
    motion_zones: list[SatelIntegraBinarySensor],
) -> None:
    """Background task to sequentially poll temperature from motion sensor zones.

    This task runs independently of HA's polling mechanism to avoid blocking.
    Requests are sent sequentially with 10-second delays to prevent overwhelming
    the alarm panel connection.
    """
    _LOGGER.info("Temperature polling task started for %d zones", len(motion_zones))

    # Wait 20 seconds before first poll to allow system to stabilize
    first_poll = True

    while True:
        try:
            if first_poll:
                _LOGGER.debug("Waiting 20 seconds before first temperature poll")
                await asyncio.sleep(20)
                first_poll = False
            else:
                # Wait full interval between subsequent polls
                await asyncio.sleep(TEMPERATURE_SCAN_INTERVAL.total_seconds())

            _LOGGER.debug("Starting temperature polling cycle for %d zones", len(motion_zones))

            for entity in motion_zones:
                # Skip zones that have been disabled (no temperature support)
                if not entity._temperature_enabled:
                    continue

                try:
                    _LOGGER.debug(
                        "Requesting temperature for zone %s ('%s')",
                        entity._device_number,
                        entity.name,
                    )

                    # Request temperature (blocks for up to 5 seconds)
                    temperature = await entity._satel.get_zone_temperature(entity._device_number)

                    if temperature is not None:
                        _LOGGER.debug(
                            "Zone %s ('%s') temperature: %.1f°C",
                            entity._device_number,
                            entity.name,
                            temperature,
                        )
                        entity._temperature = temperature
                        entity.async_write_ha_state()
                    else:
                        # Zone doesn't support temperature - disable future polling
                        _LOGGER.info(
                            "Zone %s ('%s') does not support temperature - disabling",
                            entity._device_number,
                            entity.name,
                        )
                        entity._temperature_enabled = False

                except asyncio.TimeoutError:
                    _LOGGER.debug(
                        "Timeout reading temperature for zone %s - may not support temperature",
                        entity._device_number,
                    )
                    # Disable polling for this zone
                    entity._temperature_enabled = False

                except Exception as ex:
                    _LOGGER.warning(
                        "Error reading temperature for zone %s: %s",
                        entity._device_number,
                        ex,
                    )

                # Wait before next request to avoid overwhelming connection
                await asyncio.sleep(TEMPERATURE_REQUEST_DELAY)

            _LOGGER.debug("Temperature polling cycle completed")

        except asyncio.CancelledError:
            _LOGGER.info("Temperature polling task cancelled")
            break
        except Exception as ex:
            _LOGGER.exception("Unexpected error in temperature polling task: %s", ex)
            # Continue despite errors
            await asyncio.sleep(60)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SatelConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Satel Integra binary sensor devices."""

    controller = config_entry.runtime_data

    # Collect all zone entities for temperature polling coordination
    zone_entities: list[SatelIntegraBinarySensor] = []

    zone_subentries = filter(
        lambda entry: entry.subentry_type == SUBENTRY_TYPE_ZONE,
        config_entry.subentries.values(),
    )

    for subentry in zone_subentries:
        zone_num: int = subentry.data[CONF_ZONE_NUMBER]
        zone_type: BinarySensorDeviceClass = subentry.data[CONF_ZONE_TYPE]

        entity = SatelIntegraBinarySensor(
            controller,
            config_entry.entry_id,
            subentry,
            zone_num,
            zone_type,
            SIGNAL_ZONES_UPDATED,
        )
        zone_entities.append(entity)

        async_add_entities(
            [entity],
            config_subentry_id=subentry.subentry_id,
        )

    output_subentries = filter(
        lambda entry: entry.subentry_type == SUBENTRY_TYPE_OUTPUT,
        config_entry.subentries.values(),
    )

    for subentry in output_subentries:
        output_num: int = subentry.data[CONF_OUTPUT_NUMBER]
        ouput_type: BinarySensorDeviceClass = subentry.data[CONF_ZONE_TYPE]

        async_add_entities(
            [
                SatelIntegraBinarySensor(
                    controller,
                    config_entry.entry_id,
                    subentry,
                    output_num,
                    ouput_type,
                    SIGNAL_OUTPUTS_UPDATED,
                )
            ],
            config_subentry_id=subentry.subentry_id,
        )

    # Start background task for sequential temperature polling
    # Only for motion sensor zones (IR sensors with temperature capability)
    motion_zones = [
        entity for entity in zone_entities
        if entity.device_class == BinarySensorDeviceClass.MOTION
    ]

    if motion_zones:
        _LOGGER.info(
            "Starting background temperature polling for %d motion sensor zones",
            len(motion_zones)
        )
        asyncio.create_task(_temperature_polling_task(hass, motion_zones))


class SatelIntegraBinarySensor(SatelIntegraEntity, BinarySensorEntity):
    """Representation of an Satel Integra binary sensor."""

    def __init__(
        self,
        controller: AsyncSatel,
        config_entry_id: str,
        subentry: ConfigSubentry,
        device_number: int,
        device_class: BinarySensorDeviceClass,
        react_to_signal: str,
    ) -> None:
        """Initialize the binary_sensor."""
        super().__init__(
            controller,
            config_entry_id,
            subentry,
            device_number,
        )

        self._attr_device_class = device_class
        self._react_to_signal = react_to_signal
        self._temperature: float | None = None

        # Temperature polling is handled by background task, not entity polling
        # Motion sensors start with temperature polling enabled
        # Background task will disable if zone doesn't respond with temperature
        self._temperature_enabled = (
            react_to_signal == SIGNAL_ZONES_UPDATED
            and device_class == BinarySensorDeviceClass.MOTION
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        # Call parent to handle area assignment
        await super().async_added_to_hass()

        if self._react_to_signal == SIGNAL_OUTPUTS_UPDATED:
            self._attr_is_on = self._device_number in self._satel.violated_outputs
        else:
            self._attr_is_on = self._device_number in self._satel.violated_zones

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._react_to_signal, self._devices_updated
            )
        )

    @callback
    def _devices_updated(self, zones: dict[int, int]):
        """Update the zone's state, if needed."""
        if self._device_number in zones:
            new_state = zones[self._device_number] == 1
            if new_state != self._attr_is_on:
                self._attr_is_on = new_state
                self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, float] | None:
        """Return temperature as an extra attribute if available."""
        if self._temperature is not None:
            return {"temperature": self._temperature}
        return None
