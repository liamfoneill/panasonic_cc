# Panasonic Comfort Cloud

Custom Home Assistant integration for Panasonic Comfort Cloud devices.

<p>
    <img src="https://github.com/sockless-coding/panasonic_cc/raw/master/doc/controls.png" alt="Example controls" style="vertical-align: top;max-width:100%" align="top" />
    <img src="https://github.com/sockless-coding/panasonic_cc/raw/master/doc/sensors.png" alt="Example sensors" style="vertical-align: top;max-width:100%" align="top" />
    <img src="https://github.com/sockless-coding/panasonic_cc/raw/master/doc/diagnostics.png" alt="Example diagnostics" style="vertical-align: top;max-width:100%" align="top" />
</p>

## Important

Panasonic changed the upstream authentication flow. The recommended setup now uses a Panasonic OAuth `refresh_token` instead of relying on direct Panasonic ID and password login.

This repository includes a helper script at `tools/panasonic_oauth_helper.mjs` that opens the Panasonic login page in a browser, captures the OAuth code, and exchanges it for a refresh token.

## Setup summary

1. Install the integration.
2. Run the helper script to generate a refresh token.
3. Add or reconfigure the integration in Home Assistant.
4. Paste the `refresh_token` into the config flow.

Username and password fields are still available as optional fallback fields, but the refresh token is the preferred authentication method.

#### Support Development

- [Buy me a coffee](https://www.buymeacoffee.com/sockless)
