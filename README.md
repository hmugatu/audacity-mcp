# audacity-mcp

A [Model Context Protocol](https://modelcontextprotocol.io/) server that lets Claude control [Audacity](https://www.audacityteam.org/) — open, normalize, export, label, and process audio using natural language.

```
"Normalize all tracks to -1 dB, add a label at 3.5 seconds called 'chorus', then export as FLAC."
```

## Features

- **Track inspection** — list tracks, read and set time selections
- **Effects** — normalize, amplify, fade in/out, noise reduction (two-pass, see [limitations](#known-limitations)), run saved macros
- **Export & import** — export full project or selection to WAV / FLAC / MP3 / AIFF / OGG; import audio files
- **Labels** — add, read, and export label tracks
- **Transport** — play, stop, rewind, undo

> **Note:** audacity-mcp is newly released and has been tested against the mod-script-pipe protocol specification, but not yet validated across every Audacity version in the wild. If a command doesn't behave as expected, please [open an issue](https://github.com/tachyonshuggy/audacity-mcp/issues) — fixes are very welcome.

## Prerequisites

- [Audacity](https://www.audacityteam.org/) 3.x. Tested on 3.7.9 (Linux). **Audacity 4.0 is not supported**: it ships without the scripting pipe and macros, which the Audacity team expects to bring back in 4.1.
- `mod-script-pipe` enabled: **Audacity → Preferences** (macOS) or **Edit → Preferences** (Windows/Linux) → **Modules → mod-script-pipe → Enabled**, then restart Audacity
- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

## Installation

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "audacity": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/tachyonshuggy/audacity-mcp", "audacity-mcp"]
    }
  }
}
```

Restart Claude Desktop. Audacity must be running with mod-script-pipe enabled before starting a conversation.

### From source

```bash
git clone https://github.com/tachyonshuggy/audacity-mcp
cd audacity-mcp
uv sync
uv run audacity-mcp
```

## Usage examples

Once connected, talk to Claude naturally:

- *"What tracks are in the current project?"*
- *"Normalize everything to -1 dB."*
- *"Select from 0 to 3 seconds and fade in."*
- *"Export the selection as /tmp/intro.flac."*
- *"Add a label at 12.5 seconds called 'bridge'."*
- *"Apply my CleanPodcast macro to the current selection."*

## Architecture

```
Claude ──MCP──► audacity_mcp/server.py
                      │
                      │  named pipe (mod-script-pipe)
                      ▼
                  Audacity
```

No component runs inside Audacity. The server communicates via Audacity's built-in scripting interface — a pair of named pipes that Audacity exposes when `mod-script-pipe` is enabled.

## Known limitations

- **Noise reduction** can't be configured by script. Audacity ignores
  scripted values and uses the settings last chosen in its Noise Reduction
  dialog. Each Audacity session can capture only one profile over the
  pipe, because later calls reduce noise instead. To capture a new profile,
  use **Effect → Noise Reduction → Get Noise Profile** in Audacity, then
  call `noise_reduction_apply`.
- **`export_audio` changes the selection** to the whole project, because
  Audacity's `Export2` exports only what is selected. `add_label` moves
  the selection to the new label.
- **`export_labels` writes the file itself**, on the machine running the
  server, because Audacity's `ExportLabels` opens a dialog that blocks the
  pipe.
- **File paths containing the characters `\n`** can't be sent on macOS or
  Linux, because Audacity turns them into a newline. On Windows, paths are
  sent with forward slashes to avoid this.

## Running tests

```bash
uv run pytest
```

Live tests against a running Audacity are opt-in. Open an **empty**
project first: the tests create tracks and then remove them, and they
refuse to run if the project already has tracks.

```bash
AUDACITY_LIVE=1 uv run pytest tests/test_live.py -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) — free for any use.
