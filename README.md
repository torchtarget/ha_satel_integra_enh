# Satel Integra Enhanced for Home Assistant

Enhanced custom component for Home Assistant to integrate with Satel Integra alarm systems.

## About

This is an enhanced version of the Satel Integra integration, based on the official Home Assistant component. It adds encryption support and additional protocol features not available in the official integration.

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

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations" section
3. Click the three dots menu (⋮) in the top right
4. Select "Custom repositories"
5. Add repository URL: `https://github.com/torchtarget/ha_satel_integra`
6. Select category: "Integration"
7. Click "Add"
8. Find "Satel Integra Enhanced" in the list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the `custom_components/satel_integra` directory to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

Configure via the Home Assistant UI under Settings > Devices & Services > Add Integration > Satel Integra

## Credits

- Original integration by @c-soft (Krzysztof Machelski)
- Official HA component maintained by @Tommatheussen
- Encryption library work by @wasilukm

## License

This component follows the same license as Home Assistant Core (Apache 2.0)
