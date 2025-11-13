# Home Assistant Satel Integra Custom Component

Custom component for Home Assistant to integrate with Satel Integra alarm systems.

## About

This custom component is based on the official Home Assistant Satel Integra integration with plans to add encryption support and additional protocol features.

## Current Status

**Initial Release** - This is a direct copy of the official Home Assistant component without modifications.

- Based on official HA core satel_integra component
- Uses `satel-integra==0.3.7` library (no encryption yet)
- Includes config flow for UI-based setup
- Supports partitions, zones, outputs, and switchable outputs

## Planned Features

- [ ] Add encryption support (integration_key parameter)
- [ ] Temperature monitoring
- [ ] System diagnostics/trouble sensors
- [ ] Zone bypass functionality
- [ ] Zone tamper detection
- [ ] Event log reading
- [ ] RTC/clock synchronization

## Installation

### HACS (Manual)

1. Add this repository as a custom repository in HACS
2. Install "Satel Integra Custom" from HACS
3. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/satel_integra` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

Configure via the Home Assistant UI under Settings > Devices & Services > Add Integration > Satel Integra

## Credits

- Original integration by @c-soft (Krzysztof Machelski)
- Official HA component maintained by @Tommatheussen
- Encryption library work by @wasilukm

## License

This component follows the same license as Home Assistant Core (Apache 2.0)
