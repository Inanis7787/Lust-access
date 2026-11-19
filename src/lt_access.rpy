# LT Access 0.2.1. Original accessibility code; no game assets included.
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
            lta_speak(text or "No readable text. Use the arrow keys or Tab to focus a control.")
        except Exception:
            lta_speak("Use the arrow keys or Tab to focus a control.")

    def lta_status():
        parts = ["NVDA connected" if lta_nvda_running() else "NVDA unavailable"]
        parts.append("Timed choices paused" if persistent.lt_access_pause_timers else "Timed choices running")
        for name in ("day", "day_number", "time_of_day", "location", "current_location"):
            value = getattr(renpy.store, name, None)
            if isinstance(value, (str, int, float)):
                parts.append(name.replace("_", " ") + ": " + str(value))
        for name in ("countdown", "countdownhid"):
            if renpy.get_screen(name):
                parts.append("Timed interaction available. F8 lets its timer expire; use the arrow keys or Tab and Enter to choose an action.")
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
                    renpy.hide_screen(name)
                    renpy.jump(target)
        lta_speak("No timed interaction is active.")

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
    key "K_F5" action Function(lta_silence)
    key "K_F6" action Function(lta_toggle_timers)
    key "K_F7" action Function(lta_repeat)
    key "K_F8" action Function(lta_expire_timer)

# Suppress the engine's visual self-voicing notification as well.
init offset = 10
screen _self_voicing():
    null
