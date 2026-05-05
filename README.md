# audacity-mcp

A [Model Context Protocol](https://modelcontextprotocol.io/) server that lets Claude control [Audacity](https://www.audacityteam.org/) — open, normalize, export, label, and process audio using natural language.

```
"Normalize all tracks to -1 dB, add a label at 3.5 seconds called 'chorus', then export as FLAC."
```

## Features

- **Track inspection** — list tracks, read and set time selections
- **Effects** — normalize, amplify, fade in/out, noise reduction (two-pass), run saved macros
- **Export & import** — export full project or selection to WAV / FLAC / MP3 / AIFF / OGG; import audio files
- **Labels** — add, read, and export label tracks
- **Transport** — play, stop, rewind, undo

> **Note:** audacity-mcp is newly released and has been tested against the mod-script-pipe protocol specification, but not yet validated across every Audacity version in the wild. If a command doesn't behave as expected, please [open an issue](https://github.com/tachyonshuggy/audacity-mcp/issues) — fixes are very welcome.

## Prerequisites

- [Audacity](https://www.audacityteam.org/) 3.x
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

## Running tests

```bash
uv run pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) — free for any use.
