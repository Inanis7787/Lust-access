# Speech-only menu navigation and editing. No visible mod UI.
init 991 python:
    import re as _lta_menu_re

    LTA_FIELDS = {
        "mct": ("Your in-game name", "mc_func"),
        "j_rt": ("Jessica is your", "j_r_func"),
        "m_rt": ("Megan is your", "m_r_func"),
        "s_rt": ("Elizabeth is your", "s_r_func"),
        "b_rt": ("You are Jessica and Megan's", "b_r_func"),
        "sont": ("You are Elizabeth's", "son_func"),
        "d_rt": ("Jessica and Megan are Elizabeth's", "d_r_func"),
    }
    _lta_pending_menu_speech = None

    def lta_queue_menu_speech(text):
        global _lta_pending_menu_speech
        _lta_pending_menu_speech = text

    def lta_flush_menu_speech():
        global _lta_pending_menu_speech
        if _lta_pending_menu_speech is not None:
            text = _lta_pending_menu_speech
            _lta_pending_menu_speech = None
            lta_speak(text)

    def lta_ui_label(_section, label):
        # Native focus already supplies menu context; speak the option alone.
        return _lta_menu_re.sub(r"\{[^}]*\}", "", str(label)).strip()

    def lta_field_label(field):
        return "%s: %s. Edit text" % (LTA_FIELDS[field][0], getattr(persistent, field, None) or "empty")

    def lta_editor_instructions(field):
        return (lta_field_label(field) + ". Maximum 10 characters. "
                "Type to edit, Control A to clear the field, Enter to save, Escape to cancel.")

    def lta_open_editor(field):
        renpy.show_screen("lta_edit", field=field, initial=str(getattr(persistent, field, None) or ""))
        renpy.restart_interaction()

    def lta_edit_changed(value):
        renpy.get_screen("lta_edit").scope["draft"] = value
        lta_speak(value or "empty")
        renpy.restart_interaction()

    def lta_clear_edit():
        widget = renpy.get_displayable("lta_edit", "lta_editor_input")
        widget.caret_pos = 0
        widget.update_text("", True)
        renpy.restart_interaction()

    def lta_save_edit(field, value):
        editor = renpy.get_screen("lta_edit")
        if editor is not None:
            value = editor.scope.get("draft", value)
        value = value.strip()
        if not value:
            lta_speak("The value cannot be empty. Type a value, or Escape to cancel.")
            return
        if len(value) > 10:
            lta_speak("Maximum 10 characters.")
            return
        getattr(renpy.store, LTA_FIELDS[field][1])(value)
        renpy.save_persistent()
        renpy.hide_screen("lta_edit")
        renpy.restart_interaction()
        lta_queue_menu_speech("Saved. " + lta_field_label(field))

    def lta_cancel_editor(name):
        renpy.hide_screen(name)
        renpy.restart_interaction()
        lta_queue_menu_speech("Cancelled. No changes saved.")

    def lta_help_speech():
        lta_speak("During story dialogue, Up or Down reads the current line, including voice-acted lines. Unvoiced story lines are still read automatically. In menus, arrow keys or Tab and Shift Tab move between controls. "
                  "Enter activates a button or slider. On a slider, use Left and Right, then press Enter again to finish. "
                  "Relationship fields announce their current value; Enter opens the editor. "
                  "Type to edit, Control A clears the field, Enter saves, and Escape cancels. "
                  "F2 reads screen text. F3 reads status. F5 stops speech. "
                  "F6 pauses or resumes timed choices. F7 repeats speech. "
                  "F8 takes the active timer's timeout branch.")


transform lta_invisible:
    alpha 0.0

screen lta_edit(field, initial):
    modal True
    zorder 100001
    default draft = initial
    timer 0.1 action Function(lta_speak, lta_editor_instructions(field))
    key "K_ESCAPE" action Function(lta_cancel_editor, "lta_edit")
    key "K_RETURN" action Function(lta_save_edit, field, draft)
    key "K_KP_ENTER" action Function(lta_save_edit, field, draft)
    input id "lta_editor_input" default initial changed lta_edit_changed length 10 copypaste True alt "" at lta_invisible
    key "ctrl_K_a" action Function(lta_clear_edit)
