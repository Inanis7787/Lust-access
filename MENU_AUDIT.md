# Native menu navigation — 0.2.1

The custom action list has been removed. Native arrow/Tab navigation and self-voicing remain enabled. Menu option labels no longer prepend group or section names. Relationship editing, native slider labels, save-slot labels, voice filtering, and paused timers are retained.

Validation: all 17 source tests and 39 compiled-runtime native-navigation assertions passed. The runtime checks cover plain option labels, native Tab focus, keyboard activation and saving of all seven relationship fields, native slider activation/adjustment, and native controls across the settings, save/load, help, about, voice-actress, history, and language screens.

The audit below records the earlier 0.2.0 implementation; its custom-list/group assertions do not describe the current interface.

# Historical menu audit — 0.2.0

## Source sweep

All **404 game screen definitions** were scanned. The patcher retains every original game image-button condition/action and labels all **1,608 image buttons**. Static text buttons receive section context where appropriate; dynamic labels retain their original interpolation.

The Relationship Changer's seven broken inline input bindings are deliberately replaced with labelled editor actions. Save slots and page controls receive explicit names. Adjustable settings bars are included in the spoken control list; viewport scrollbars are omitted because the list exposes off-screen controls directly.

The audit covers UI declarations, not every possible unlocked story state. Game-generated UI overrides are not committed to this repository.

## Runtime menu sweep

Tests ran inside a separate game copy with a separate save directory. The user's running game and saves were not used. Synthetic events were sent through Ren'Py's own screen/input handlers; this does not certify physical-key operation or replace NVDA user testing.

**140 engine assertions passed** across the following menus. The compiled-only release subsequently passed the same 140 checks in a second isolated game/save directory:

| Menu | Controls in test state |
| --- | ---: |
| Main menu | 8 |
| Settings | 22 |
| Relationship Changer | 16 |
| Character voices | 18 |
| Save | 28 |
| Load | 28 |
| Help | 12 |
| About | 9 |
| Voice actresses | 13 |
| Dialogue history | 9 |
| Language | 5 |

Control counts include the relevant navigation/Back controls and vary with game state.

## Verified behavior

- All seven relationship fields accept actual text-input events, clear with Ctrl+A, and commit through the original game callbacks.
- Enter saves edits and Escape discards them; saved values receive speech confirmation.
- Settings sliders announce values, apply changes on Enter, and discard drafts on Escape.
- Empty save/load slots remain discoverable, with unavailable state announced.
- Save-page selectors and the page-name control have meaningful labels.
- Repeated actress links include the appropriate actress name.
- Each tested menu renders and exposes labelled, grouped controls; Up, Home, End, and group navigation work through engine key events.
- Earlier checks covered paused visible/hidden timers, NVDA controller calls, and selective narration of unvoiced dialogue.

## Limits

This is not a 100% completion certification. Every story route, unlocked bonus menu state, achievement, rollback/save combination, language, physical-key configuration, and interaction with other mods has not been exhaustively tested. Image-only phone messages and visual scene descriptions remain outside this version.

## Scanned declaration counts

- `bar`: 6
- `button`: 9
- `imagebutton`: 1608
- `input`: 3
- `textbutton`: 457
- `vbar`: 13
- `viewport`: 14
