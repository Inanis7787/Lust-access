# LT Access 0.2.0. Original accessibility code; no game assets included.
default persistent.lt_access_pause_timers = True

init 990 python:
    import ctypes as _lta_ctypes
    import os as _lta_os

    _lta_original_tts = config.tts_function
    _lta_nvda = None
    _lta_last = ""
    _lta_speech_ok = False
    _lta_speech_error = None
    try:
        _lta_nvda = _lta_ctypes.WinDLL(_lta_os.path.join(config.basedir, "nvdaControllerClient64.dll"))
        _lta_nvda.nvdaController_testIfRunning.argtypes = []
        _lta_nvda.nvdaController_testIfRunning.restype = _lta_ctypes.c_long
        _lta_nvda.nvdaController_speakText.argtypes = [_lta_ctypes.c_wchar_p]
        _lta_nvda.nvdaController_speakText.restype = _lta_ctypes.c_long
        _lta_nvda.nvdaController_cancelSpeech.argtypes = []
        _lta_nvda.nvdaController_cancelSpeech.restype = _lta_ctypes.c_long
    except Exception as _lta_exc:
        _lta_speech_error = str(_lta_exc)
        _lta_nvda = None

    def lta_nvda_running():
        try:
            return _lta_nvda is not None and _lta_nvda.nvdaController_testIfRunning() == 0
        except Exception:
            return False

    def lta_dialogue_is_voiced():
        # Resolve this say statement's voice, rather than checking whether
        # any audio happens to be playing. The result survives a short clip
        # ending while the same dialogue remains on screen.
        if not config.has_voice:
            return False
        try:
            info = _get_voice_info()
            filename = info.filename
            if not filename or not renpy.loadable(filename, directory="audio"):
                return False
            if info.tag in (persistent._voice_mute or set()):
                return False
            if not persistent._character_volume.get(info.tag, 1.0):
                return False
            if _preferences.get_mute("voice") or _preferences.get_volume("voice") <= 0:
                return False
            return True
        except Exception:
            # Missing/invalid voice metadata must not silence unvoiced text.
            return False

    def lta_speak(text):
        global _lta_last, _lta_speech_ok, _lta_speech_error
        text = str(text).strip()
        if text:
            _lta_last = text
        if lta_nvda_running():
            try:
                _lta_nvda.nvdaController_cancelSpeech()
                if text:
                    result = _lta_nvda.nvdaController_speakText(text)
                    _lta_speech_ok = result == 0
                    if result:
                        raise RuntimeError("NVDA speech error %s" % result)
                return
            except Exception as exc:
                _lta_speech_error = str(exc)
        return None

    def lta_repeat():
        lta_speak(_lta_last or "No text has been spoken yet.")

    def lta_silence():
        if lta_nvda_running():
            _lta_nvda.nvdaController_cancelSpeech()
        else:
            _lta_original_tts("")

    def lta_read():
        try:
            text = renpy.display.tts.root._tts_all()
            lta_speak(text or "No readable text. Press F4 for available actions.")
        except Exception:
            lta_speak("Press F4 for available actions.")

    def lta_status():
        parts = ["NVDA connected" if lta_nvda_running() else "NVDA unavailable"]
        parts.append("Timed choices paused" if persistent.lt_access_pause_timers else "Timed choices running")
        for name in ("day", "day_number", "time_of_day", "location", "current_location"):
            value = getattr(renpy.store, name, None)
            if isinstance(value, (str, int, float)):
                parts.append(name.replace("_", " ") + ": " + str(value))
        for name in ("countdown", "countdownhid"):
            if renpy.get_screen(name):
                parts.append("Timed interaction available. F8 lets its timer expire; choose an action with F4.")
        lta_speak(". ".join(parts))

    def lta_toggle_timers():
        persistent.lt_access_pause_timers = not persistent.lt_access_pause_timers
        renpy.save_persistent()
        renpy.restart_interaction()
        lta_status()

    def lta_expire_timer():
        for name in ("countdown", "countdownhid"):
            screen = renpy.get_screen(name)
            if screen:
                target = screen.scope.get("timer_jump")
                if target and renpy.has_label(target):
                    renpy.hide_screen("lta_actions")
                    renpy.hide_screen(name)
                    renpy.jump(target)
        lta_speak("No timed interaction is active.")

    def lta_available_actions():
        # Use only the currently rendered screens, respecting modal boundaries.
        # Do not jump to labels or expose story actions which are not available.
        entries = list(renpy.game.context().scene_lists.layers.get("screens", []))
        found = []
        seen = set()
        for entry in reversed(entries):
            screen = entry.displayable
            name = getattr(screen, "screen_name", ("",))[0]
            if name.startswith("lta_"):
                continue
            buttons = []
            screen.visit_all(lambda d: buttons.append(d) if isinstance(d, renpy.display.behavior.Button) else None)
            for button in buttons:
                action = button.action if button.action is not None else button.clicked
                if action is None or not button.is_sensitive():
                    continue
                try:
                    text = button._tts_all().strip()
                except Exception:
                    text = ""
                if not text:
                    text = name.replace("_", " ") + " action"
                # Preserve separate actions with identical labels.
                signature = (id(button), text)
                if signature in seen:
                    continue
                seen.add(signature)
                found.append((text, action))
            if getattr(screen, "modal", False):
                break
        return found

    def lta_open_actions():
        if renpy.get_screen("lta_actions"):
            renpy.hide_screen("lta_actions")
        else:
            items = lta_available_actions()
            renpy.show_screen("lta_actions", items=items)
        renpy.restart_interaction()

    def lta_announce_action(items, position):
        if items:
            lta_speak("%d of %d. %s" % (position + 1, len(items), items[position][0]))
        else:
            lta_speak("No actions available. Press Escape, then Space to advance dialogue.")

    def lta_help_speech():
        lta_speak("Accessibility help. Arrow keys or Tab move between game controls. Enter activates. "
                  "Space advances dialogue. F2 reads the screen. F3 reads status. "
                  "F4 opens or closes the spoken action list. In that list use Up and Down, "
                  "Home and End, or Page Up and Page Down, then Enter to choose. Escape closes it. "
                  "F5 stops speech. F6 pauses or resumes timers. F7 repeats speech. "
                  "F8 takes the current timer's timeout branch, which may be a failure. "
                  "Timers start paused. V toggles speech.")

    config.tts_function = lta_speak
    config.tts_voice_channels = []
    _preferences.self_voicing = True
    # Tab normally enables skipping. With this mod it moves keyboard focus.
    config.keymap["toggle_skip"] = [k for k in config.keymap["toggle_skip"] if k != "K_TAB"]
    config.keymap["focus_down"] = list(config.keymap["focus_down"]) + ["K_TAB"]
    config.keymap["focus_up"] = list(config.keymap["focus_up"]) + ["shift_K_TAB"]
    config.always_shown_screens.append("lta_keys")

screen lta_keys():
    zorder 100002
    timer 0.15 repeat True action Function(lta_flush_menu_speech)
    key "K_F1" action Function(lta_help_speech)
    key "K_F2" action Function(lta_read)
    key "K_F3" action Function(lta_status)
    key "K_F4" action Function(lta_open_actions)
    key "K_F5" action Function(lta_silence)
    key "K_F6" action Function(lta_toggle_timers)
    key "K_F7" action Function(lta_repeat)
    key "K_F8" action Function(lta_expire_timer)

screen lta_actions(items):
    zorder 100001
    modal True
    default position = 0
    key "K_ESCAPE" action Hide("lta_actions")
    key "K_F4" action Hide("lta_actions")
    timer 0.1 action Function(lta_announce_action, items, position)
    if items:
        key "K_DOWN" action [SetScreenVariable("position", (position+1)%len(items)), Function(lta_announce_action, items, (position+1)%len(items))]
        key "K_TAB" action [SetScreenVariable("position", (position+1)%len(items)), Function(lta_announce_action, items, (position+1)%len(items))]
        key "K_UP" action [SetScreenVariable("position", (position-1)%len(items)), Function(lta_announce_action, items, (position-1)%len(items))]
        key "shift_K_TAB" action [SetScreenVariable("position", (position-1)%len(items)), Function(lta_announce_action, items, (position-1)%len(items))]
        key "K_HOME" action [SetScreenVariable("position", 0), Function(lta_announce_action, items, 0)]
        key "K_END" action [SetScreenVariable("position", len(items)-1), Function(lta_announce_action, items, len(items)-1)]
        key "K_PAGEDOWN" action [SetScreenVariable("position", min(position+10,len(items)-1)), Function(lta_announce_action, items, min(position+10,len(items)-1))]
        key "K_PAGEUP" action [SetScreenVariable("position", max(position-10,0)), Function(lta_announce_action, items, max(position-10,0))]
        key "K_RETURN" action [Hide("lta_actions"), items[position][1]]
        key "K_KP_ENTER" action [Hide("lta_actions"), items[position][1]]

# Suppress the engine's visual self-voicing notification as well.
init offset = 10
screen _self_voicing():
    null
