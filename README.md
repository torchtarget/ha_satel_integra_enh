# Satel Integra Enhanced for Home Assistant

Enhanced custom component for Home Assistant to integrate with Satel Integra alarm systems.

## About

This is an enhanced version of the Satel Integra integration, based on the official Home Assistant component. It adds encryption support and additional protocol features not available in the official integration.

## Current Status

**v0.5.0 - Temperature Monitoring!** - Now supports reading temperature from temperature-enabled zones.

- Based on official HA core satel_integra component
- Uses enhanced `satel_integra_enh` library with extended protocol support
- Updated to new library API with improved lifecycle management
- **✅ Encryption support via integration_key parameter**
- **✅ Automatic area assignment for zones and outputs**
- **✅ Temperature monitoring for temperature-capable zones**
- Includes config flow for UI-based setup
- Supports YAML configuration for easy bulk setup
- Supports partitions, zones, outputs, and switchable outputs

## Features

- **Encrypted Communication**: Supports integration key for secure communication with your alarm panel
- **Automatic Area Assignment**: Assign devices to Home Assistant areas directly from configuration
- **Temperature Monitoring**: Read temperature from zones with temperature sensors
- **YAML Configuration**: Configure all zones, partitions, and outputs via YAML for easy bulk setup
- **Alarm Control Panel**: Arm/disarm partitions with different modes (Away, Home)
- **Binary Sensors**: Monitor zone states (doors, windows, motion detectors, etc.)
- **Switches**: Control switchable outputs (gates, lights, etc.)
- **Real-time Updates**: Instant notifications when zone states change
- **Multi-Partition Support**: Manage multiple alarm partitions independently

## Planned Features

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
5. Add repository URL: `https://github.com/torchtarget/ha_satel_integra_enh`
6. Select category: "Integration"
7. Click "Add"
8. Find "Satel Integra Enhanced" in the list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the `custom_components/satel_integra` directory to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

This integration supports two configuration methods:

### Method 1: YAML Configuration (Recommended for Bulk Setup)

Configure the integration via `configuration.yaml` for easy management of many zones:

```yaml
satel_integra:
  host: 192.168.1.100  # IP address of your ETHM-1 Plus module
  port: 7094  # Optional, defaults to 7094
  integration_key: !secret satel_integration_key  # Optional, for encryption

  # Configure partitions
  partitions:
    "01":
      name: "Perimeter"
      arm_home_mode: 1  # Optional: 1, 2, or 3
    "02":
      name: "Inside"
      arm_home_mode: 1

  # Configure zones with optional area assignment
  zones:
    1: { name: "Front Door", type: door, area: "entry" }
    2: { name: "Kitchen Motion", type: motion, area: "kitchen" }
    3: { name: "Living Room Window", type: window, area: "living_room" }
    4: { name: "Basement Smoke Detector", type: smoke, area: "basement" }
    5: { name: "Outdoor Temperature", type: motion, area: "garden" }
    # ... add all your zones

  # Configure outputs (read-only monitoring)
  outputs:
    1: { name: "Siren Status", type: motion, area: "entry" }

  # Configure switchable outputs (controllable switches)
  switchable_outputs:
    5: { name: "Garage Door", area: "garage" }
    6: { name: "Gate Control", area: "entry" }
```

**Area Assignment Features:**
- **Optional**: The `area` parameter is completely optional
- **Auto-create**: If an area doesn't exist, Home Assistant will automatically create it
- **Simple names**: Use plain text names like "kitchen", "living_room", "basement"
- **All device types**: Works for zones, outputs, and switchable outputs

**Available Zone Types:**
- `motion` - Motion detectors (default)
- `door` - Door contacts
- `window` - Window contacts
- `smoke` - Smoke detectors
- `tamper` - Tamper sensors
- `panic` - Panic buttons

**Temperature Monitoring (Automatic):**
Temperature sensors are automatically detected and created for zones that support temperature readings. No configuration is required!
- During setup, each zone is tested for temperature capability
- If a zone supports temperature, a temperature sensor entity is automatically created
- Temperature is reported in Celsius
- Sensor polls every 60 seconds
- Temperature range: -55°C to +125°C (0.5°C increments)

Example - if zone 10 has a temperature sensor:
```yaml
zones:
  10: { name: "Basement", type: motion, area: "basement" }
```

This automatically creates:
- `binary_sensor.basement` - Motion sensor
- `sensor.basement_temperature` - Temperature sensor (auto-detected)

After adding the configuration, restart Home Assistant to load the changes.

### Method 2: UI Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **"Satel Integra"**
3. Enter the following information:
   - **Host**: IP address of your ETHM-1 Plus module
   - **Port**: TCP port (default: 7094)
   - **Code** (optional): Alarm code for controlling switchable outputs
   - **Integration Key** (optional): Encryption key for secure communication
4. Click **Submit**
5. Add partitions, zones, outputs, and switchable outputs as needed

**Note**: UI configuration does not support area assignment. Use YAML configuration for automatic area assignment.

### Finding Your Integration Key

The integration key (also called "integration password") is configured on your Satel Integra panel:
1. Enter installer mode on your alarm panel
2. Navigate to the ETHM-1 Plus module settings
3. Look for "Integration" or "INTEGRATION" settings
4. The integration key is a string/password (e.g., `svamneUw6XCg` or similar)

**Note**: If your panel requires encryption and you don't provide the integration key, the connection will fail with "No response received from panel" errors.

## Credits

- Original integration by @c-soft (Krzysztof Machelski)
- Official HA component maintained by @Tommatheussen
- Encryption library work by @wasilukm

## License

This component follows the same license as Home Assistant Core (Apache 2.0)
