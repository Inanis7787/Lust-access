# Lust Access

**An accessibility mod for Lust Theory — Season 1.**

Lust Access makes *Lust Theory — Season 1* more accessible to blind and visually impaired players using NVDA on Windows. It adds spoken menus, keyboard navigation, dialogue handling, and accessible controls for timed choices.

**Tested with:**
- Ren'Py 8.1.3.23091805
- Windows 64-bit
- NVDA

## A note about the code

Full disclosure ,I did not write  or read a single line of code and don't intend to for this project lol. Everything you see was done by Codex.

If it works, fantastic. If something breaks, open an issue. Just remember that AI-generated code isn't magically immune lmao.

## Features

### Dialogue and voice acting

Lust Access is designed to work alongside the game's existing voice acting rather than talk over it.

- **Voiced dialogue:** NVDA automatically avoids reading dialogue when a playable voice-acting clip is available.
- **Unvoiced dialogue:** Spoken through NVDA.
- **Descriptions and narration:** Read aloud when no corresponding voice clip is available.
- **Missing or muted voice clips:** Fall back to NVDA speech.
- **Menus and controls:** Spoken with keyboard navigation.

### Accessible navigation

Menus use the game's native focus navigation with self-voicing enabled. Options are spoken without added menu or section prefixes: for example, "Start". For sliders, focus the control, press Enter, adjust with Left/Right, then press Enter again to finish.

The mod provides a keyboard-driven interface for navigating supported game menus, making selections, reviewing screen text, and handling timed events.

Timed choices are paused by default so you don't have to race against a timer while listening to NVDA.

## Installation

### Automatic installation (recommended)

1. Close Lust Theory if it's running.
2. Download and extract [LT_Access_0.2.1.zip](https://github.com/Inanis7787/Lust-access/raw/refs/heads/main/release/LT_Access_0.2.1.zip) from the `release/` folder.
3. Run `Install.cmd` from the extracted folder.
4. Launch the game normally.

**Requirement:** Python 3.10 or newer must be installed to run the installer or uninstaller.

The default game directory is:

`C:\GOG Games\Lust Theory - Season 1`

### Installing to a different directory

If your game is installed somewhere else, run:

```powershell
py -3 install_access.py --game "C:\path\to\Lust Theory - Season 1"
```

### NVDA requirements

The game directory must already contain a compatible `nvdaControllerClient64.dll`.

This project does not redistribute that DLL.

If the mod cannot establish a connection to NVDA, it will remain silent rather than interfere with the game.

### Uninstallation

1. Close the game.
2. Run `Uninstall.cmd`.
3. Follow the prompts.

The installer preserves the original game archives and verifies file hashes before removing the mod.

**Important:** Uninstall an older release before installing a newer one. Existing local installations updated in place do not require a fresh installation.

## Keyboard controls

| Key | Action |
|---|---|
| F1 | Read keyboard help |
| F2 | Read the current screen text |
| F3 | Announce NVDA connection and game status |
| Up / Down | Move between controls |
| Tab / Shift+Tab | Move forward or backward through controls |
| Enter | Activate the selected control; press again to finish adjusting a slider |
| Escape | Close the editor or open the game menu |
| F5 | Stop NVDA speech |
| F6 | Pause or resume timed choices |
| F7 | Repeat the last speech |
| F8 | Immediately trigger the active timer's timeout branch |
| Space | Advance dialogue |
| V | Toggle speech |
| Ctrl (hold) | Skip dialogue |

### Timed choices

Timed choices begin paused automatically.

Use the arrow keys or Tab to review the available controls, then press Enter to choose.

Press `F6` to pause or resume the timer manually.

Press `F8` to take the timeout branch immediately.

**Warning:** The timeout branch isn't necessarily the correct option. Depending on the scene, it can result in failure.

### A note about Tab

The Tab key is reserved for accessible focus navigation. Hold Ctrl to skip dialogue instead.

## Known limitations

This is an accessibility mod, not a complete remake of the game's interface.

Current limitations include:

- Image-only phone messages are not transcribed.
- Visual scenes are not described.
- Some information conveyed exclusively through images may remain inaccessible.
- Game updates may break compatibility.
- Other UI mods may conflict with the accessibility overrides.
- NVDA connectivity depends on the compatible controller DLL being available.

The mod was developed and tested against the specified Ren'Py version. Compatibility with other versions is not guaranteed.

See [MENU_AUDIT.md](MENU_AUDIT.md) for the menu testing and validation scope.

## Building from source

For anyone who wants to tinker, the source is available.

### Run the tests

```powershell
py -3 -m unittest discover -s src/tests -v
```

### Build a release

The release builder uses the installed game's Ren'Py runtime.

```powershell
py -3 src/build_release.py --game-root "C:\GOG Games\Lust Theory - Season 1"
```

The build process compiles only the two mod scripts in an isolated temporary directory and generates a distributable release bundle and ZIP in `release/`.

The installer can also be run directly from `src/` for a source installation.

## Research and acknowledgments

Implementation was informed by the following projects and documentation:

- [Ren'Py Self-Voicing Documentation](https://www.renpy.org/doc/html/self_voicing.html)
- [Ren'Py Accessibility Add-On](https://minute.itch.io/renpy-accessibility)

Engine compatibility was checked against the installed Ren'Py 8.1.3 source.

## Issues and contributions

If you encounter broken menus, missing speech, navigation problems, or anything else that makes the game difficult to play with NVDA, please open a GitHub issue.

When reporting a problem, include the game version, what you were attempting to do, what happened, and what you expected to happen.

Pull requests and accessibility improvements are welcome.

## License

Lust Access is released under the **MIT License**.

Game content and third-party libraries remain the property of their respective owners and retain their original licenses.

This project is an unofficial accessibility modification and is not affiliated with the developers or publishers of *Lust Theory*.

---

*Made because I wanted to play the damn game, not because I wanted to become a Ren'Py developer.*

*Code by Codex. Accessibility first. Bullshit kept to a minimum.*
