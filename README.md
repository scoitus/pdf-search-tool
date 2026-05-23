# PDF Search Tool

A macOS desktop app for searching text across large collections of PDF files. Supports plain text, regular expression, and boolean search modes with a fast, multi-threaded engine powered by PyMuPDF.

## Features

- **Three search modes** — Plain text, Regular expression, and Boolean (`AND` / `OR` / `NOT` with phrase quoting and parentheses grouping)
- **Case-sensitive option** — toggle per search
- **Multi-source search** — mix and match folders and individual PDF files in a single search
- **Recursive subdirectory search** — toggle on/off for folder sources
- **Recently searched folders** — quick access to the last 10 folders used
- **Live results** — matches stream in as each file is processed
- **In-context snippets** — view surrounding text for each match
- **Open in Preview** — jump directly to the matching page
- **Reveal in Finder** — locate the source file quickly
- **Saved profiles** — save and reload named search configurations (query, folders, mode, options)

## Requirements

- macOS (the Preview and Finder integrations are macOS-only)
- Python 3.11 or later

## Setup

Clone the repo, create a virtual environment, and install dependencies:

```bash
git clone <repo-url>
cd pdf-search-tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running from source

Activate the virtual environment and launch:

```bash
source .venv/bin/activate
python src/main.py
```

> You need to run `source .venv/bin/activate` each time you open a new terminal session before launching the app.

## Building a standalone macOS app

A [PyInstaller](https://pyinstaller.org/) spec file is used to produce a self-contained `.app` bundle (no Python installation required to run it):

```bash
source .venv/bin/activate
./scripts/build.sh
```

The built app is placed at `dist/PDF Search Tool.app`.

### Installing the built app

```bash
./scripts/install.sh
```

> **Note:** `scripts/install.sh` has a hardcoded destination path (`/Applications/_MY APPS/PDF Search Tool.app`). Edit that path in the script before running if you want to install elsewhere.

## Project structure

```
src/
├── main.py                  # Entry point
├── search_engine.py         # PDF text extraction and search logic (PyMuPDF)
├── boolean_parser.py        # Boolean query parser (AND / OR / NOT / phrases)
├── profile_manager.py       # Save/load search profiles (JSON, ~/.config/)
├── preview_opener.py        # macOS Preview and Finder integration
├── gui/
│   ├── main_window.py       # Top-level application window
│   ├── search_panel.py      # Left panel: query, mode, folders, options
│   ├── folder_list_widget.py
│   ├── recent_folders_widget.py
│   ├── results_panel.py     # Right panel: results tree and snippets
│   ├── profile_dialog.py    # Save / Load profile dialogs
│   └── styles.py            # Dark-mode QSS stylesheet
├── models/
│   ├── search_result.py     # Result data classes
│   └── search_profile.py    # Profile data class
└── workers/
    └── search_worker.py     # Background search thread (QThread)

scripts/
├── build.sh                 # PyInstaller build
└── install.sh               # Copy built app to Applications
```

## Boolean search syntax

| Example | Meaning |
|---|---|
| `climate AND policy` | Both terms must appear |
| `climate OR weather` | Either term |
| `climate AND NOT draft` | climate present, draft absent |
| `"exact phrase" AND summary` | Quoted phrases matched literally |
| `(policy OR regulation) AND NOT draft` | Grouping with parentheses |

Operator precedence: `NOT` > `AND` > `OR`

## Saved profiles

Use **Profiles › Save Current Search** (`⌘S`) to save the current query, folders, mode, and options under a name. Reload any saved profile with **Profiles › Load Profile** (`⌘O`).

Profiles are stored at `~/.config/pdf-search-tool/profiles.json`.
