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
    LTA_TITLES = {
        "main_menu": "Main menu", "preferences": "Settings", "relation_change": "Relationship Changer",
        "save": "Save game", "load": "Load game", "history": "Dialogue history", "help": "Game help",
        "vo_act": "Voice actresses", "mute_person": "Character voices", "choose_lang_main": "Language",
        "quest_menu": "Quest hints", "cell_phone_menu": "Phone", "hidden_menu": "Hidden scenes",
        "relive_menu": "Replay", "gallery_menu": "Gallery", "cheat_menu": "Bonus options",
        "confirm": "Confirmation", "about": "About", "nicole_phone": "Phone messages",
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

    def lta_ui_label(section, label):
        def clean(value):
            return _lta_menu_re.sub(r"\{[^}]*\}", "", str(value)).strip()
        section, label = clean(section), clean(label)
        return (section + ": " if section else "") + label

    def lta_field_label(field):
        return "%s: %s. Edit text" % (LTA_FIELDS[field][0], getattr(persistent, field, None) or "empty")

    def lta_editor_instructions(field):
        return (lta_field_label(field) + ". Maximum 10 characters. "
                "Type to edit, Control A to clear the field, Enter to save, Escape to cancel.")

    def lta_open_editor(field):
        renpy.hide_screen("lta_actions")
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

    def lta_adjust_label(label, adjustment, value=None):
        value = adjustment.value if value is None else value
        percent = int(round(100.0 * value / adjustment.range)) if adjustment.range else 0
        return "%s: %d percent" % (label, percent)

    def lta_open_adjustment(label, adjustment):
        renpy.hide_screen("lta_actions")
        renpy.show_screen("lta_adjust", label=label, adjustment=adjustment, initial=adjustment.value)
        renpy.restart_interaction()

    def lta_adjust_change(label, adjustment, value):
        value = max(0, min(adjustment.range, value))
        renpy.get_screen("lta_adjust").scope["draft"] = value
        lta_speak(lta_adjust_label(label, adjustment, value))
        renpy.restart_interaction()

    def lta_adjust_save(label, adjustment, value):
        editor = renpy.get_screen("lta_adjust")
        if editor is not None:
            value = editor.scope.get("draft", value)
        adjustment.change(adjustment.round_value(value, release=True))
        renpy.hide_screen("lta_adjust")
        renpy.restart_interaction()
        lta_queue_menu_speech("Saved. " + lta_adjust_label(label, adjustment))

    def lta_available_actions():
        entries = list(renpy.game.context().scene_lists.layers.get("screens", []))
        found, seen = [], set()
        for entry in reversed(entries):
            screen = entry.displayable
            name = getattr(screen, "screen_name", ("",))[0]
            if name.startswith("lta_") or name == "_self_voicing":
                continue
            title = LTA_TITLES.get(name, name.replace("_", " ").capitalize())
            controls = []
            screen.visit_all(lambda d: controls.append(d) if isinstance(d, (renpy.display.behavior.Button, renpy.display.behavior.Bar)) else None)
            for control in controls:
                if id(control) in seen:
                    continue
                seen.add(id(control))
                group = title
                if isinstance(control, renpy.display.behavior.Bar):
                    adjustment = control.adjustment
                    if not adjustment.adjustable:
                        continue
                    # Viewport scrollbars are navigation plumbing, not settings.
                    if control.value is not None and control.value.__class__.__name__ in ("YScrollValue", "XScrollValue"):
                        continue
                    label = str(control.style.alt or "Adjust value")
                    action = Function(lta_open_adjustment, label, adjustment)
                    text = lta_adjust_label(label, adjustment)
                else:
                    action = control.action if control.action is not None else control.clicked
                    if action is None:
                        continue
                    enabled = control.is_sensitive()
                    try:
                        text = control._tts_all().strip()
                    except Exception:
                        text = ""
                    if not text:
                        text = title + " action"
                    if text.startswith("Navigation: "):
                        text, group = text[len("Navigation: "):], "Navigation"
                    elif text.startswith("Return to previous"):
                        group = "Back"
                    if not enabled:
                        text += ". Unavailable"
                        action = Function(lta_queue_menu_speech, text)
                found.append((text, action, group))
            if getattr(screen, "modal", False):
                break
        # Keep content in the authored order, followed by menu navigation/back.
        return sorted(found, key=lambda item: 2 if item[2] == "Back" else 1 if item[2] == "Navigation" else 0)

    def lta_open_actions():
        for name in ("lta_edit", "lta_adjust"):
            if renpy.get_screen(name):
                lta_speak("Finish editing with Enter, or cancel with Escape.")
                return
        if renpy.get_screen("lta_actions"):
            renpy.hide_screen("lta_actions")
            lta_speak("Action list closed.")
        else:
            renpy.show_screen("lta_actions", items=lta_available_actions())
        renpy.restart_interaction()

    def lta_announce_action(items, position):
        if items:
            item = items[position]
            group = item[2] if len(item) > 2 else "Actions"
            lta_speak("%s. %d of %d. %s" % (group, position + 1, len(items), item[0]))
        else:
            lta_speak("No actions available. Escape closes the list. Use F2 to read text or Space to advance dialogue.")

    def lta_group_position(items, position, direction):
        if not items:
            return 0
        group = items[position][2] if len(items[position]) > 2 else "Actions"
        for delta in range(1, len(items)+1):
            index = (position + delta*direction) % len(items)
            other = items[index][2] if len(items[index]) > 2 else "Actions"
            if other != group:
                return index
        return position

    def lta_help_speech():
        lta_speak("F4 opens a spoken list of the current menu's controls. "
                  "Up and Down move through items. Left and Right change groups. "
                  "Home and End go to the first and last item. Page Up and Page Down move ten items. "
                  "Enter activates, Escape closes. Relationship fields announce their current value; "
                  "Enter opens an editor, then Enter saves and Escape cancels. "
                  "Slider controls open an editor: arrows adjust, Enter saves, Escape cancels. "
                  "F2 reads screen text. F3 reads status. F5 stops speech. F6 toggles timed choices. "
                  "F7 repeats speech. F8 takes a timer's timeout branch.")

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

screen lta_adjust(label, adjustment, initial):
    modal True
    zorder 100001
    default draft = initial
    $ increment = adjustment.range / 20.0
    timer 0.1 action Function(lta_speak, lta_adjust_label(label, adjustment, draft) + ". Arrows adjust by five percent. Enter saves. Escape cancels.")
    key "K_ESCAPE" action Function(lta_cancel_editor, "lta_adjust")
    key "K_RETURN" action Function(lta_adjust_save, label, adjustment, draft)
    key "K_KP_ENTER" action Function(lta_adjust_save, label, adjustment, draft)
    key "K_LEFT" action Function(lta_adjust_change, label, adjustment, draft-increment)
    key "K_DOWN" action Function(lta_adjust_change, label, adjustment, draft-increment)
    key "K_RIGHT" action Function(lta_adjust_change, label, adjustment, draft+increment)
    key "K_UP" action Function(lta_adjust_change, label, adjustment, draft+increment)
    key "K_HOME" action Function(lta_adjust_change, label, adjustment, 0)
    key "K_END" action Function(lta_adjust_change, label, adjustment, adjustment.range)

init offset = 20
screen lta_actions(items):
    zorder 100001
    modal True
    default position = 0
    key "K_ESCAPE" action Hide("lta_actions")
    timer 0.1 action Function(lta_announce_action, items, position)
    if items:
        key "K_DOWN" action [SetScreenVariable("position", (position+1)%len(items)), Function(lta_announce_action, items, (position+1)%len(items))]
        key "K_TAB" action [SetScreenVariable("position", (position+1)%len(items)), Function(lta_announce_action, items, (position+1)%len(items))]
        key "K_UP" action [SetScreenVariable("position", (position-1)%len(items)), Function(lta_announce_action, items, (position-1)%len(items))]
        key "shift_K_TAB" action [SetScreenVariable("position", (position-1)%len(items)), Function(lta_announce_action, items, (position-1)%len(items))]
        key "K_LEFT" action [SetScreenVariable("position", lta_group_position(items,position,-1)), Function(lta_announce_action,items,lta_group_position(items,position,-1))]
        key "K_RIGHT" action [SetScreenVariable("position", lta_group_position(items,position,1)), Function(lta_announce_action,items,lta_group_position(items,position,1))]
        key "K_HOME" action [SetScreenVariable("position", 0), Function(lta_announce_action, items, 0)]
        key "K_END" action [SetScreenVariable("position", len(items)-1), Function(lta_announce_action, items, len(items)-1)]
        key "K_PAGEDOWN" action [SetScreenVariable("position", min(position+10,len(items)-1)), Function(lta_announce_action, items, min(position+10,len(items)-1))]
        key "K_PAGEUP" action [SetScreenVariable("position", max(position-10,0)), Function(lta_announce_action, items, max(position-10,0))]
        key "K_RETURN" action [Hide("lta_actions"), items[position][1]]
        key "K_KP_ENTER" action [Hide("lta_actions"), items[position][1]]
