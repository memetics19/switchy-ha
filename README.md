# Switchy for Home Assistant

A local-only Home Assistant integration for [Switchy](https://switchy.in) ESP32 touch panels.
It talks to each panel over your LAN, with no cloud and no vendor app in the loop.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=memetics19&repository=switchy-ha&category=integration)

One click on the badge adds this repository to [HACS](https://hacs.xyz) on your own Home
Assistant. Then install Switchy and restart.

Each panel channel appears as a switch entity. Control is immediate and polling keeps the state
in sync.

## Install

### HACS (custom repository)

1. HACS, then the three-dot menu, then Custom repositories.
2. Add this repository, category Integration.
3. Install Switchy, then restart Home Assistant.

### Manual

Copy `custom_components/switchy` into your Home Assistant `config/custom_components` directory
and restart.

## Add a panel

Settings, then Devices and services, then Add integration, then Switchy. Enter the panel's
device id (on its sticker, or from the Switchy app) and its address on your network. Repeat for
each panel.

## How it works

The integration speaks the panel's offline protocol: a status read and an AES-CFB command, the
same the Switchy app uses on the local network. Nothing leaves your network.

## Security note

The panel's command key is derived from the device id it serves unauthenticated, so anyone on
the same LAN can control it. Put the panels on a trusted network segment.

## Limitations

- Channels are exposed as switches. Fan-speed channels are on the roadmap.
- Panels are reached by address; if your DHCP moves them, give them reservations or re-add.

## License

MIT. Not affiliated with [Switchy](https://switchy.in); "Switchy" refers to the panels this talks to.
