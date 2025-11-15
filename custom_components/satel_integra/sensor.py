"""Support for Satel Integra temperature sensors."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from satel_integra_enh import AsyncSatel

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_ENABLE_TEMPERATURE,
    CONF_ZONE_NUMBER,
    SUBENTRY_TYPE_ZONE,
    SatelConfigEntry,
)
from .entity import SatelIntegraEntity

_LOGGER = logging.getLogger(__name__)

# Temperature polling interval - 5 minutes to avoid overwhelming the connection
TEMPERATURE_SCAN_INTERVAL = timedelta(minutes=5)

# Delay between sequential temperature requests (10 seconds)
TEMPERATURE_REQUEST_DELAY = 10


async def _temperature_polling_task(
    hass: HomeAssistant,
    temperature_sensors: list[SatelIntegraTemperatureSensor],
) -> None:
    """Background task to sequentially poll temperature from configured zones.

    This task runs independently of HA's polling mechanism to avoid blocking.
    Requests are sent sequentially with 10-second delays to prevent overwhelming
    the alarm panel connection. Only zones with enable_temperature=True are polled.
    """
    _LOGGER.info("Temperature polling task started for %d zones", len(temperature_sensors))

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

            _LOGGER.debug("Starting temperature polling cycle for %d zones", len(temperature_sensors))

            for sensor in temperature_sensors:
                # Skip sensors that have been disabled (no temperature support)
                if not sensor._temperature_enabled:
                    continue

                # Check if connection is healthy before requesting
                if not sensor._satel.connected:
                    _LOGGER.warning(
                        "Connection lost during temperature polling - stopping cycle"
                    )
                    break

                try:
                    _LOGGER.debug(
                        "Requesting temperature for zone %s ('%s')",
                        sensor._zone_number,
                        sensor.name,
                    )

                    # Request temperature (blocks for up to 5 seconds)
                    temperature = await sensor._satel.get_zone_temperature(sensor._zone_number)

                    if temperature is not None:
                        _LOGGER.debug(
                            "Zone %s ('%s') temperature: %.1f°C",
                            sensor._zone_number,
                            sensor.name,
                            temperature,
                        )
                        sensor._attr_native_value = temperature
                        sensor.async_write_ha_state()
                    else:
                        # Zone doesn't support temperature - disable future polling
                        _LOGGER.info(
                            "Zone %s ('%s') does not support temperature - disabling",
                            sensor._zone_number,
                            sensor.name,
                        )
                        sensor._temperature_enabled = False
                        # Give connection extra time to recover after no-response
                        await asyncio.sleep(5)

                except asyncio.TimeoutError:
                    _LOGGER.warning(
                        "Timeout reading temperature for zone %s - may not support temperature",
                        sensor._zone_number,
                    )
                    # Disable polling for this sensor
                    sensor._temperature_enabled = False
                    # Give connection extra time to recover after timeout
                    _LOGGER.debug("Pausing 30 seconds after timeout to allow connection recovery")
                    await asyncio.sleep(30)

                except Exception as ex:
                    _LOGGER.warning(
                        "Error reading temperature for zone %s: %s",
                        sensor._zone_number,
                        ex,
                    )
                    # Give connection time to recover after error
                    await asyncio.sleep(30)

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
    """Set up the Satel Integra temperature sensor devices."""

    controller = config_entry.runtime_data

    # Collect temperature sensor entities for zones with enable_temperature=True
    temperature_sensors: list[SatelIntegraTemperatureSensor] = []

    zone_subentries = filter(
        lambda entry: entry.subentry_type == SUBENTRY_TYPE_ZONE,
        config_entry.subentries.values(),
    )

    for subentry in zone_subentries:
        # Only create temperature sensors for zones with enable_temperature=True
        if not subentry.data.get(CONF_ENABLE_TEMPERATURE, False):
            continue

        zone_num: int = subentry.data[CONF_ZONE_NUMBER]

        sensor = SatelIntegraTemperatureSensor(
            controller,
            config_entry.entry_id,
            subentry,
            zone_num,
        )
        temperature_sensors.append(sensor)

        async_add_entities(
            [sensor],
            config_subentry_id=subentry.subentry_id,
        )

    # Start background task for sequential temperature polling
    if temperature_sensors:
        _LOGGER.info(
            "Starting background temperature polling for %d temperature sensors",
            len(temperature_sensors)
        )
        asyncio.create_task(_temperature_polling_task(hass, temperature_sensors))


class SatelIntegraTemperatureSensor(SatelIntegraEntity, SensorEntity):
    """Representation of a Satel Integra temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1
    _attr_should_poll = False  # Updated by background task, not HA polling

    def __init__(
        self,
        controller: AsyncSatel,
        config_entry_id: str,
        subentry: ConfigSubentry,
        zone_number: int,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(
            controller,
            config_entry_id,
            subentry,
            zone_number,
        )

        # Override unique_id to include _temperature suffix
        self._attr_unique_id = f"{config_entry_id}_zone_{zone_number}_temperature"

        # Override name to include "Temperature" suffix
        self._attr_name = f"{subentry.data['name']} Temperature"

        self._zone_number = zone_number
        self._attr_native_value: float | None = None

        # Temperature polling is enabled by default (zone was configured with enable_temperature=True)
        # Background task will disable if zone doesn't respond with temperature
        self._temperature_enabled = True
