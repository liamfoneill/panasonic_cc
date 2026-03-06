# Panasonic Comfort Cloud for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Integration Usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&style=for-the-badge&logo=home-assistant&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.panasonic_cc.total)](https://analytics.home-assistant.io/)

Custom Home Assistant integration for Panasonic Comfort Cloud air conditioners, heat pumps, and supported Aquarea devices.

> [!IMPORTANT]
> Panasonic changed its authentication flow. Direct Panasonic ID and password login is no longer reliable for this integration.
>
> The recommended setup is:
> 1. Generate a Panasonic OAuth `refresh_token` with the included helper script.
> 2. Paste that token into the integration config flow in Home Assistant.
>
> Username and password fields remain available as fallback fields, but the refresh token is the primary authentication method now.

<p>
    <img src="https://github.com/sockless-coding/panasonic_cc/raw/master/doc/controls.png" alt="Example controls" style="vertical-align: top;max-width:100%" align="top" />
    <img src="https://github.com/sockless-coding/panasonic_cc/raw/master/doc/sensors.png" alt="Example sensors" style="vertical-align: top;max-width:100%" align="top" />
    <img src="https://github.com/sockless-coding/panasonic_cc/raw/master/doc/diagnostics.png" alt="Example diagnostics" style="vertical-align: top;max-width:100%" align="top" />
</p>

## Features

- Climate entities for Panasonic air conditioners and heat pumps
- Horizontal swing mode selection
- Sensors for inside and outside temperature where available
- Nanoe, ECONAVI, and AI ECO switches where available
- Optional daily energy sensors
- Calculated current power sensor from energy readings
- Zone controls where available
- Aquarea support for compatible devices

## Installation

### HACS

1. Install [HACS](https://hacs.xyz/docs/setup/download) if it is not already installed.
2. Add this repository as a custom integration or open it directly:
   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sockless-coding&repository=panasonic_cc&category=integration)
3. Download the integration from HACS.
4. Restart Home Assistant.
5. Start the config flow:
   [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=panasonic_cc)

### Manual install

Copy `custom_components/panasonic_cc` into your Home Assistant `custom_components` directory and restart Home Assistant.

## Authentication Setup

### Recommended: refresh token

Generate a Panasonic refresh token once, then use that token in Home Assistant.

1. Prepare a temporary Node/Playwright environment:

```bash
mkdir -p /tmp/pwprobe
cd /tmp/pwprobe
npm init -y
npm install playwright
npx playwright install chromium
```

2. Run the helper script from that directory:

```bash
cd /tmp/pwprobe
node /path/to/panasonic_cc/tools/panasonic_oauth_helper.mjs /tmp/panasonic-refresh-token.json
```

Example for this repository checkout:

```bash
cd /tmp/pwprobe
node /Users/Liam/Developer/GitHub/panasonic_cc/tools/panasonic_oauth_helper.mjs /tmp/panasonic-refresh-token.json
```

3. A Chromium window will open. Complete the Panasonic login manually, including any MFA steps.
4. When the script reports success, copy the `refresh_token` value from the JSON output.
5. In Home Assistant, add or reconfigure the Panasonic Comfort Cloud integration and paste the token into the `refresh_token` field.

Use only the `refresh_token`. Do not paste the `access_token` or `id_token` into Home Assistant.

### If the token expires

If Panasonic revokes or expires the refresh token, the integration will stop authenticating. Run the helper again to generate a fresh token, then reconfigure the integration with the new value.

## Home Assistant Configuration

The config flow now accepts:

- `refresh_token`: recommended and preferred
- `username` and `password`: optional compatibility fields
- Daily energy and polling options

![Setup](https://github.com/sockless-coding/panasonic_cc/raw/master/doc/setup.png)

After the initial setup, the following options are available:

![Options](https://github.com/sockless-coding/panasonic_cc/raw/master/doc/configuration.png)

## Known Limitations

- Panasonic's legacy username/password login flow is unreliable due to upstream authentication changes.
- Refresh tokens are currently the stable authentication path.
- If the refresh token expires or is revoked, it must be regenerated with the helper script.

## Dependencies

- [`aio-panasonic-comfort-cloud`](https://github.com/sockless-coding/aio-panasonic-comfort-cloud)
- [`aioaquarea`](https://github.com/cjaliaga/aioaquarea)

## Support Development

- [Buy me a coffee](https://www.buymeacoffee.com/sockless)

[license-shield]: https://img.shields.io/github/license/sockless-coding/panasonic_cc.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/sockless-coding/panasonic_cc.svg?style=for-the-badge
[releases]: https://github.com/sockless-coding/panasonic_cc/releases
