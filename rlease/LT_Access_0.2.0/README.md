# Lust Access

NVDA accessibility mod for the GOG version of **Lust Theory — Season 1**, tested with Ren'Py 8.1.3.23091805 on 64-bit Windows.

Version **0.2.0** adds an accessible Relationship Changer and reorganizes spoken menu navigation. This is a work in progress: a full playthrough of every route and bonus scene has **not** been verified.

## Folders

- `src/`: mod source, installer, release builder, and automated tests.
- `rlease/`: compiled `.rpyc` files, installer bundle, ZIP, and checksums. The folder spelling follows the requested layout.

Only the mod's original code is distributed. The installer generates UI overrides from the user's own game archive. Game assets, story scripts, screen-reader DLLs, and saves are not included.

## Install

1. Close the game and start NVDA.
2. Extract `rlease/LT_Access_0.2.0.zip`.
3. Run `Install.cmd` inside the extracted folder. Python 3.10 or newer is required for installation/removal.
4. Launch the game normally.

Default game location: `C:\GOG Games\Lust Theory - Season 1`.

For another location:

```powershell
py -3 install_access.py --game "C:\path\to\Lust Theory - Season 1"
```

The game folder must already contain a compatible `nvdaControllerClient64.dll`. This project does not redistribute that library. The mod stays silent if it cannot connect to NVDA.

To remove, close the game and run `Uninstall.cmd`. The installer preserves the original archives and checks its file hashes before removal. Uninstall an older version before installing a new release. A locally updated existing installation does not need reinstalling.

## NVDA and speech

No visible mod buttons, action panels, help text, or self-voicing banner are drawn. NVDA automatically skips dialogue with an available, unmuted voice-acting clip, even after that clip finishes. Unvoiced dialogue, descriptions, and menu controls remain spoken. Missing or muted clips fall back to NVDA.

If NVDA intercepts game keys, switch it to focus mode where supported.

| Key | Action |
| --- | --- |
| F1 | Speak keyboard help |
| F2 | Read current screen text |
| F3 | Read connection/game status |
| F4 | Open or close the spoken control list |
| Up/Down or Tab/Shift+Tab | Move through controls |
| Left/Right in the F4 list | Move between content, navigation, and Back groups |
| Home/End | First/last control |
| Page Up/Page Down | Move ten controls |
| Enter | Activate the current control |
| Escape | Close the list/editor or open the game menu |
| F5 | Stop speech |
| F6 | Pause/resume timed choices |
| F7 | Repeat speech |
| F8 | Take the active timer's timeout branch; this can be a failure |
| Space | Advance dialogue |
| V | Toggle speech |

Timed choices start paused. Use F4 to react, or F8 to let the timer expire. Hold Ctrl to skip dialogue; Tab is reserved for focus navigation.

## Relationship Changer

From the in-game Settings menu, choose Change Relationships. Press F4, choose a field, and press Enter. Each field announces its label and current value.

- Type to edit; **Ctrl+A clears the field**.
- Enter saves through the game's original callback.
- Escape discards the draft.
- Empty values and values longer than ten characters are rejected.

The editor is invisible and communicates through NVDA. The seven fields cover the player name and the game's existing relationship labels; it does not add new story settings.

## Other menus

The spoken list includes labelled settings sliders, numbered save/load slots, explicit save-page names, and context for repeated links. Empty/disabled controls are announced as unavailable. Content comes first, then navigation, then Back.

Choose a slider from F4 to edit it. Arrow keys change its draft value by five percent; Home/End select the minimum/maximum. Enter applies it; Escape cancels. Use the game's original save/load confirmation prompts normally.

## Build and test

Run source tests:

```powershell
py -3 -m unittest discover -s src/tests -v
```

Build the compiled release using your installed game runtime:

```powershell
py -3 src/build_release.py --game-root "C:\GOG Games\Lust Theory - Season 1"
```

The build compiles only the two mod scripts in an isolated temporary directory, then produces the bundle in `rlease/`. The installer can also run directly from `src/` for a source installation.

See [MENU_AUDIT.md](MENU_AUDIT.md) for the menu sweep and validation scope. Image-only phone messages are not transcribed, and the project does not provide visual scene descriptions. Game updates and other UI mods may conflict with these overrides.

## Research and license

Implementation was informed by [Ren'Py self-voicing documentation](https://www.renpy.org/doc/html/self_voicing.html), the [Vigil accessibility mod](https://github.com/EarthboundPromoter/Vigil), and the [Ren'Py Accessibility Add-On](https://minute.itch.io/renpy-accessibility). Engine compatibility was checked against the installed 8.1.3 source.

The mod's original code is MIT licensed. Game content and third-party libraries retain their original licenses.
