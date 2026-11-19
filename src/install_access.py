"""Reversible accessibility patcher for the installed GOG Ren'Py 8.1.3 build.

Reads UI source from the user's own archive. Includes no extracted game content.
Usage: python install_access.py [--game PATH] [--uninstall]
"""
import argparse
import ast
import hashlib
import io
import json
import pathlib
import pickle
import re
import tokenize
import zlib

VERSION = "0.2.1"
HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_GAME = pathlib.Path(r"C:\GOG Games\Lust Theory - Season 1")


class IndexReader(pickle.Unpickler):
    def find_class(self, module, name):
        raise ValueError("Unexpected object in archive index")


def archive_sources(path):
    with path.open("rb") as f:
        header = f.readline().split()
        if header[0] != b"RPA-3.0":
            raise ValueError("Unsupported archive format")
        offset, key = (int(x, 16) for x in header[1:3])
        f.seek(offset)
        index = IndexReader(io.BytesIO(zlib.decompress(f.read()))).load()
        result = {}
        for name, chunks in index.items():
            if "/" in name or "\\" in name or not name.endswith(".rpy"):
                continue
            data = b""
            for chunk in chunks:
                pos, size = chunk[0] ^ key, chunk[1] ^ key
                if pos < 0 or size < 0 or pos + size > offset:
                    raise ValueError("Invalid archive extent")
                f.seek(pos)
                data += (chunk[2] if len(chunk) > 2 else b"") + f.read(size)
            result[name] = data.decode("utf-8-sig")
        return result


WORDS = {
    "meg": "Megan", "jess": "Jessica", "eliz": "Elizabeth", "nic": "Nicole",
    "m": "Megan", "j": "Jessica", "s": "Elizabeth", "z": "Zoe",
    "e": "Ellie", "t": "Taylor", "ss": "Sophie", "n": "Nicole",
    "morn": "morning", "afnoon": "afternoon", "afn": "afternoon", "eve": "evening",
    "liv": "living room", "kit": "kitchen", "sbath": "school bathroom",
    "pc": "computer", "lapt": "laptop", "hosp": "hospital", "liq": "liquor store",
    "vic": "clothing store", "stripc": "club", "closer": "close", "hid": "hidden",
    "eng": "English", "ger": "German", "spa": "Spanish", "rus": "Russian", "chi": "Chinese",
    "b": "", "r": "room", "p1": "part 1", "p2": "part 2", "p3": "part 3",
}


def readable(value):
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    words = re.split(r"[_\s]+", value)
    result = " ".join(WORDS.get(w.lower(), w) for w in words if w.lower() not in
                      {"button", "icon", "idle", "hover", "png", "%s"})
    return re.sub(r"\s+", " ", result).strip().capitalize()


def code_without_comment(line):
    # Tokenizer recognizes # inside quoted strings correctly.
    try:
        for tok in tokenize.generate_tokens(io.StringIO(line).readline):
            if tok.type == tokenize.COMMENT:
                return line[:tok.start[1]].rstrip(), line[tok.start[1]:]
    except (tokenize.TokenError, IndentationError):
        pass
    return line.rstrip(), ""


def tooltip_labels(sources):
    result = {}
    for source in sources.values():
        for match in re.finditer(r"^screen\s+(\w+)[^\n]*:\s*\n((?:[ \t]+[^\n]*\n|\n)*)", source, re.M):
            text = re.search(r'\btext\s+_?\(?\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', match[2])
            if text:
                try:
                    value = ast.literal_eval(text[1])
                    value = re.sub(r"\{[^}]*\}", "", value)
                    if value.strip():
                        result[match[1]] = value.strip()
                except (ValueError, SyntaxError):
                    pass
    return result


def button_label(line, screen, tooltips):
    hover = re.search(r'hovered\s+Show\(["\']([^"\']+)', line)
    if hover and hover[1] in tooltips and not any(x in hover[1] for x in ("block", "message")):
        return tooltips[hover[1]], "tooltip"
    image = re.search(r'\b(?:auto|idle)\s+["\']([^"\']+)', line)
    if image:
        value = pathlib.PurePosixPath(image[1]).stem.replace("%s", "")
        fixed = {"forward_button_": "Advance time", "travel_button_": "Travel menu",
                 "cell_phone_icon_button_": "Open phone", "cell_phone_off_button_": "Put phone away",
                 "lang_choice_eng_": "English", "lang_choice_ger_": "German (unavailable)",
                 "lang_choice_spa_": "Spanish", "lang_choice_rus_": "Russian", "lang_choice_chi_": "Chinese"}
        if value in fixed:
            return fixed[value], "explicit label"
        value = readable(value)
        if value:
            return value, "asset name"
    jump = re.search(r'\b(?:Jump|Show|ShowMenu)\(["\']([^"\']+)', line)
    return readable(jump[1] if jump else screen) + " action", "action name"


def patch_source(source, tooltips):
    lines = source.splitlines()
    result, controls = [], []
    screen = ""
    screens = 0
    section_labels = []
    relation_field = None
    for number, line in enumerate(lines, 1):
        match = re.match(r"screen\s+(\w+)", line)
        if match:
            screen = match[1]
            screens += 1
            section_labels = []
            relation_field = None
        code, comment = code_without_comment(line)
        indent = len(line) - len(line.lstrip())
        if code.strip() and not code.lstrip().startswith('#'):
            section_labels = [(level, title) for level, title in section_labels if level <= indent]
        literal = r'''(?:_(\s*\(\s*)?\s*)?("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')'''
        heading = re.match(r'\s*label\s+' + literal, code)
        if heading:
            quoted = heading[2]
            section_labels = [(level, title) for level, title in section_labels if level != indent]
            if '[' not in ast.literal_eval(quoted):
                section_labels.append((indent, quoted))
        if screen == 'relation_change':
            field = re.search(r'\bid "input_(\w+)"', code)
            if field:
                relation_field = {'mct':'mct','j_rt':'j_rt','m_rt':'m_rt','s_rt':'s_rt','b_rt':'b_rt','sont':'sont','d_rt':'d_rt'}[field[1]]
                result.append(line)
                result.append(' ' * indent + 'alt lta_field_label(' + repr(relation_field) + ')')
                continue
            if relation_field and code.strip() == 'action NullAction()':
                line = ' ' * indent + 'action Function(lta_open_editor, ' + repr(relation_field) + ')'
            if re.match(r'\s*add Input\(default=persistent\.', code):
                line = ' ' * indent + 'text (persistent.' + relation_field + ' or "")'
        textbutton = re.match(r'\s*textbutton\s+' + literal, code)
        if textbutton and not re.search(r'\balt\s', code) and ('[' not in ast.literal_eval(textbutton[2]) or screen == 'file_slots'):
            quoted = textbutton[2]
            caption = ast.literal_eval(quoted)
            section = section_labels[-1][1] if section_labels else "''"
            expression = 'lta_ui_label(_(%s), _(%s))' % (section, quoted)
            if screen == 'file_slots':
                expression = {'<':repr('Previous save page'), '>':repr('Next save page'),
                              '{#auto_page}A':repr('Automatic saves'), '{#quick_page}Q':repr('Quick saves'),
                              '[page]':'("Save page %s" % page)'}.get(caption, expression)
            suffix = ':' if code.endswith(':') else ''
            line = (code[:-1].rstrip() if suffix else code) + ' alt ' + expression + suffix + (' '+comment if comment else '')
        if re.match(r'\s*bar\s+value\b', code) and section_labels:
            line = code + ' alt _(' + section_labels[-1][1] + ')' + (' '+comment if comment else '')
        if re.match(r"\s*imagebutton\b", code) and not re.search(r"\balt\s", code):
            label, method = button_label(code, screen, tooltips)
            # Labels come from the user's installed UI. Avoid interpolation.
            label = label.replace("[", "[[")
            suffix = ":" if code.endswith(":") else ""
            if suffix:
                code = code[:-1].rstrip()
            code += " alt " + repr(label) + suffix
            controls.append({"line": number, "screen": screen, "label": label, "source": method})
            line = code + (" " + comment if comment else "")
        if screen in ("countdown", "countdownhid") and re.match(r"\s*timer\s+time\b", code):
            indent = line[:len(line)-len(line.lstrip())]
            result.append(indent + "if not persistent.lt_access_pause_timers:")
            line = "    " + line
        result.append(line)
        if screen == 'file_slots' and code.strip() == 'action FileAction(slot)':
            result.append(' ' * indent + 'alt ("Slot %s. %s. %s" % (slot, FileTime(slot, format="%A, %B %d %Y, %H:%M", empty="Empty slot"), FileSaveName(slot)))')
        if screen == 'file_slots' and code.strip() == 'action page_name_value.Toggle()':
            result.append(' ' * indent + 'alt ("Rename save page: %s" % page_name_value.get_text())')
        if screen == "say" and line == "    window:":
            result.append('        alt ("" if lta_dialogue_is_voiced() else None)')
    return "\n".join(result) + "\n", controls, screens


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screen_blocks(source):
    """Copy UI definitions only, retaining original compiled story identifiers."""
    lines = source.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        if re.match(r'^screen\s', lines[i]):
            start = i
            i += 1
            while i < len(lines):
                line = lines[i]
                if line.strip() and not line.lstrip().startswith('#') and not line[0].isspace():
                    break
                i += 1
            blocks.append('\n'.join(lines[start:i]))
        else:
            i += 1
    return blocks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=pathlib.Path, default=DEFAULT_GAME)
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    root = args.game.resolve()
    game = root / "game"
    manifest_path = game / "lt_access_manifest.json"
    if args.uninstall:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for name, expected in manifest["files"].items():
            path = game / name
            if path.parent.resolve() != game or path.name != name:
                raise ValueError("Invalid manifest path")
            if path.exists() and digest(path) != expected:
                raise RuntimeError("File was edited after installation; refusing to remove: " + name)
        for name in manifest["files"]:
            path = game / name
            path.unlink(missing_ok=True)
            if path.suffix == ".rpy":
                path.with_suffix(".rpyc").unlink(missing_ok=True)
        manifest_path.unlink()
        print("LT Access removed. Original archives and saves retained. Press V to disable built-in speech if needed.")
        return
    if manifest_path.exists():
        raise RuntimeError("Already installed. Uninstall before reinstalling.")
    sources = archive_sources(game / "scr.rpa")
    tips = tooltip_labels(sources)
    writes = {}
    for name in ('lt_access.rpy', 'lt_access_menu.rpy'):
        source = HERE / name
        compiled = source.with_suffix('.rpyc')
        if source.exists():
            writes[name] = source.read_text(encoding='utf-8')
        elif compiled.exists():
            writes[compiled.name] = compiled.read_bytes()
        else:
            raise FileNotFoundError('Missing bundled mod script: ' + name)
    overrides = ['# UI-only overrides generated from the locally installed game.',
                 '# Later priority than the original screen definitions.', 'init offset = 10', '']
    report = {"version": VERSION, "screens": 0, "image_buttons": 0, "files": {}}
    for name, source in sources.items():
        if not re.search(r"^screen\s", source, re.M):
            continue
        patched, controls, screens = patch_source(source, tips)
        overrides.extend(screen_blocks(patched))
        report["screens"] += screens
        report["image_buttons"] += len(controls)
        report["files"][name] = controls
    writes["lt_access_screens.rpy"] = '\n\n'.join(overrides) + '\n'
    writes["lt_access_coverage.json"] = json.dumps(report, indent=2, ensure_ascii=True)
    for name in writes:
        candidates = [game/name]
        if pathlib.Path(name).suffix in ('.rpy', '.rpyc'):
            candidates = [(game/pathlib.Path(name).with_suffix(suffix)) for suffix in ('.rpy', '.rpyc')]
        if any(path.exists() for path in candidates):
            raise RuntimeError("Existing loose mod file would be overwritten: " + name)
    manifest = {"version": VERSION, "files": {}}
    try:
        for name, content in writes.items():
            path = game / name
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8", newline="\n")
            manifest["files"][name] = digest(path)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception:
        for name in manifest["files"]:
            (game/name).unlink(missing_ok=True)
        raise
    print("Installed LT Access %s: %d image button labels across %d screens." %
          (VERSION, report["image_buttons"], report["screens"]))
    print("Start NVDA, launch the game, and press F1 for keyboard help.")


if __name__ == "__main__":
    main()
