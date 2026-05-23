"""Open PDFs in macOS Preview at a specific page, and reveal in Finder.

Background
----------
Modern macOS Preview does NOT expose ``current page`` or any other page-
navigation property to AppleScript — the dictionary only carries the
standard suite (document, window, name, path, …). Earlier versions of
this module tried ``set current page of theDoc to page N`` and silently
failed with a syntax error; PDFs opened but always landed on page 1.

The reliable workaround is to drive the **Go → Go to Page…** menu via
System Events: click the menu item, fill in the page number, click OK.

Cold-launch gotcha
------------------
``tell application "Preview" to activate`` returns before Preview is
actually ready to receive script commands. The next ``open POSIX file``
in the same script gets misrouted (in practice we saw
``AXVisualSupportAgent got an error: Application isn't running``).
The fix is to open the file via the shell (``open -a Preview <path>``),
which Launch Services handles correctly whether Preview is cold or warm,
then run the page-navigation AppleScript afterwards.

Permissions
-----------
Driving the menu requires Accessibility permission for the host process
(Terminal when running from source, the .app bundle when packaged). The
first invocation prompts the user. If permission is denied the file
still opens — it just won't auto-navigate to the matched page.
"""

import os
import subprocess


def open_pdf_at_page(file_path: str, page_number: int):
    """Open ``file_path`` in Preview and navigate to ``page_number`` (1-based)."""
    abs_path = os.path.abspath(file_path)
    page_num = max(1, int(page_number))

    # Step 1: open the file via Launch Services. Works for both cold and
    # warm Preview, returns essentially immediately.
    subprocess.run(
        ["open", "-a", "Preview", abs_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    # Step 2: wait for Preview/document to be ready, then drive the Go to
    # Page dialog. Spawned as a detached process so we don't block the
    # caller (the GUI thread).
    as_path = abs_path.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
    set targetPath to "{as_path}"
    set targetPage to {page_num}

    -- Wait for Preview process to be up and frontmost with a window.
    tell application "System Events"
        repeat 80 times
            if exists process "Preview" then
                tell process "Preview"
                    if frontmost and (count of windows) > 0 then exit repeat
                end tell
            end if
            delay 0.1
        end repeat
    end tell

    -- Wait until the matching document is actually loaded (not just any
    -- document, in case the user already had others open).
    tell application "Preview"
        set foundDoc to false
        repeat 60 times
            try
                repeat with i from 1 to (count of documents)
                    if (path of document i) is targetPath then
                        set foundDoc to true
                        exit repeat
                    end if
                end repeat
            end try
            if foundDoc then exit repeat
            delay 0.1
        end repeat
    end tell

    -- Drive Go → Go to Page…. Wrapped in try so a missing Accessibility
    -- grant doesn't break the open-file behavior above.
    try
        tell application "System Events"
            tell process "Preview"
                click menu item "Go to Page…" of menu "Go" of menu bar 1
                repeat 30 times
                    if exists sheet 1 of window 1 then exit repeat
                    delay 0.05
                end repeat
                tell sheet 1 of window 1
                    set value of text field 1 to (targetPage as text)
                    click button "OK"
                end tell
            end tell
        end tell
    end try
    '''
    subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def reveal_in_finder(file_path: str):
    """Reveal a file in Finder."""
    subprocess.Popen(
        ["open", "-R", file_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
