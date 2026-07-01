# FinTrack

<p align="center">
    <a href="https://github.com/KosteQ314/FinTrack/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/KosteQ314/FinTrack"></a>
    <a href="https://github.com/KosteQ314/FinTrack/graphs/commit-activity"><img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/t/KosteQ314/FinTrack?color=neongreen"></a>
</p>

> *Your personal financial command center for the verse.*

Track income, expenses and profits across Star Citizen with a financial management platform.

## Features

- **Full GUI app** — session management, transaction tracking, player splits, CSV export
- **In-game overlay** — always-on-top input panel, summon with `F9`
- **Voice control** — log transactions hands-free with natural voice commands
- **CLI** — lightweight command line interface for quick edits
- **Profit splitting** — equal, percentage, and fixed splits across players

## Installation

### Installer
Download the latest [release](https://github.com/KosteQ314/FinTrack/releases) and run `FinTrack-Setup.exe`.

The installer includes:
- **FinTrack App** — full app with GUI, overlay, and voice control (required)
- **FinTrack CLI** — lightweight command line interface (optional)

### Portable
Alternatively download the portable versions — extract the zip and run the exe directly, no installation needed.

- `FinTrack.zip` — full app with GUI, overlay, and voice control
- `FinTrack-CLI.zip` — lightweight command line interface

### Running from source

```bash
git clone https://github.com/KosteQ314/FinTrack
cd FinTrack
pip install -r requirements.txt
python run.py
```

### Voice control setup

Voice control requires the Vosk speech model. Download `vosk-model-small-en-us-0.15` from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) and place it in the root `FinTrack` folder.

### Hotkeys

| Hotkey | Action |
|--------|--------|
| `F9` | Show/hide overlay |
| `F7` | Toggle overlay mode in app |
| `F8` | Push-to-talk (when voice mode is set to hotkey) |

All hotkeys can be changed in `config.json`.

### Voice commands

Wake word: `fin` (configurable in `config.json`)

`fin log [income|expense] <description> for <amount>`

**Examples:**
`fin log expense refuel for fourteen hundred`
`fin log income cargo for fifty thousand`
`fin log expense repairs for five thousand`

Descriptions must match one of the known keywords (refuel, fuel, repair, cargo, bounty, salvage, mining, delivery, etc.). The amount can be spoken as a number word or digit sequence. Both `always-on` and `push-to-talk` modes are supported and can be toggled from the system tray.

## Roadmap

- [x] Transaction tracking
- [x] Player income splitting
- [x] Voice control
- [x] Overlay
- [x] GUI
- [x] Transaction timestamps
- [x] CSV export
- [x] Installer
- [ ] Voice control improvements
- [ ] Organisation support

## Contributing

**Contributions are definitely welcome** as I'm doing it fully alone currently and my current programming knowledge is scarce.

### Support

If you enjoy FinTrack and want to support development, consider buying me a coffee!

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/M8F022E71O)\
Any support is greatly appreciated and motivates me to keep working and improving the project knowing that people are invested in it.

## License

This project is licensed under the MIT License.
