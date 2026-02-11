"""Open PDFs in macOS Preview at a specific page."""

import subprocess
import shlex


def open_pdf_at_page(file_path: str, page_number: int):
    """Open a PDF in macOS Preview at a specific page.

    Uses `open -a Preview` followed by AppleScript to navigate
    to the target page.
    """
    subprocess.Popen(["open", "-a", "Preview", file_path])

    applescript = f'''
    delay 0.8
    tell application "Preview"
        activate
        set theDoc to front document
        set theWindows to every window
        if (count of theWindows) > 0 then
            tell front window
                -- Go to the specified page
                set current page of theDoc to page {page_number} of theDoc
            end tell
        end if
    end tell
    '''
    subprocess.Popen(["osascript", "-e", applescript])


def reveal_in_finder(file_path: str):
    """Reveal a file in Finder."""
    subprocess.Popen(["open", "-R", file_path])
