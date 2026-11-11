# PDF Search Tool

A macOS desktop app for searching text across large collections of PDF files. Supports plain text, regular expression, and boolean search modes with a fast, multi-threaded engine powered by PyMuPDF.

## Features

- **Three search modes** — Plain text, Regular expression, and Boolean (`AND` / `OR` / `NOT` with phrase quoting and parentheses grouping)
- **Case-sensitive option** — toggle per search
- **Multi-source search** — mix and match folders and individual PDF files in a single search
- **Recursive subdirectory search** — toggle on/off for folder sources
- **Recently searched folders** — quick access to the last 10 folders used
- **Live results** — matches stream in as each file is processed
- **In-context snippets** — each match shows its surrounding text with the term highlighted
- **Page peek** — hover (or arrow-key to) a result to see the actual PDF page region in a floating preview, with the match highlighted
- **Built-in page viewer** — click a result to read the full page beside the list, step through matches, change pages and zoom
- **Sort and group results** — by order found, name, match count or date modified; grouped by file or by folder
- **Drag and drop** — drop folders or PDFs anywhere in the window to add them
- **Light and dark themes** — follows the macOS appearance setting
- **Open in Preview** — jump directly to the matching page
- **Reveal in Finder** — locate the source file quickly
- **Saved profiles** — save and reload named search configurations (query, folders, mode, options)

## Requirements

- macOS (the Preview and Finder integrations are macOS-only)
- Python 3.11 or later

> **First-run permission prompt:** opening a PDF at a specific page drives
> Preview's "Go to Page…" dialog via macOS UI scripting, so the first time
> you double-click a result, macOS will ask to grant the host app
> Accessibility permission (under **System Settings → Privacy & Security →
> Accessibility**). When running from source the host is Terminal; the
> packaged `.app` requests it under its own name. If you decline, PDFs
> still open — they just won't auto-navigate to the matched page.

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
│   ├── search_bar.py        # Top bar: query, mode, match case, Search
│   ├── search_panel.py      # Sidebar: folders/files to search, recent
│   ├── pdf_preview.py       # Page rendering + floating preview of a match
│   ├── page_viewer.py       # Side pane showing the full page for a match
│   ├── folder_list_widget.py
│   ├── recent_folders_widget.py
│   ├── results_panel.py     # Right panel: results grouped by file
│   ├── profile_dialog.py    # Save / Load profile dialogs
│   └── styles.py            # Light/dark theme colors and QSS stylesheet
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
