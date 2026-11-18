import importlib.util
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import tempfile
import unittest
import zlib

SOURCE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',SOURCE/'install_access.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def archive(game, text):
    raw=text.encode()
    head=b'RPA-3.0 0000000000000000 00000000\n'
    index={'fixture.rpy':[(len(head),len(raw),b'')]}
    (game/'scr.rpa').write_bytes(('RPA-3.0 %016x 00000000\n'%(len(head)+len(raw))).encode()+raw+zlib.compress(pickle.dumps(index)))


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.root=Path(self.temporary.name);self.game=self.root/'game';self.game.mkdir()
        archive(self.game,'screen sample():\n    vbox:\n        label _("Sound")\n        textbutton _("Test") action NullAction()\n        imagebutton auto "close_%s.png" action Return()\n')
        self.command=[sys.executable,str(SOURCE/'install_access.py'),'--game',str(self.root)]

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self,*extra,command=None):
        return subprocess.run((command or self.command)+list(extra),capture_output=True,text=True)

    def test_reversible_source_install(self):
        original=(self.game/'scr.rpa').read_bytes()
        (self.game/'keep.txt').write_text('user file')
        self.assertEqual(self.run_cli().returncode,0)
        manifest=json.loads((self.game/'lt_access_manifest.json').read_text())
        self.assertIn('lt_access_menu.rpy',manifest['files'])
        self.assertIn('Sound',(self.game/'lt_access_screens.rpy').read_text())
        (self.game/'lt_access.rpyc').write_bytes(b'generated')
        self.assertNotEqual(self.run_cli().returncode,0)
        self.assertEqual(self.run_cli('--uninstall').returncode,0)
        self.assertEqual((self.game/'scr.rpa').read_bytes(),original)
        self.assertEqual((self.game/'keep.txt').read_text(),'user file')
        self.assertFalse((self.game/'lt_access.rpyc').exists())

    def test_existing_mod_is_protected(self):
        (self.game/'lt_access_menu.rpy').write_text('user edit')
        self.assertNotEqual(self.run_cli().returncode,0)
        self.assertEqual((self.game/'lt_access_menu.rpy').read_text(),'user edit')

    def test_uninstall_checks_all_hashes_before_removing_any_file(self):
        self.assertEqual(self.run_cli().returncode,0)
        (self.game/'lt_access_menu.rpy').write_text('user edit')
        self.assertNotEqual(self.run_cli('--uninstall').returncode,0)
        self.assertTrue((self.game/'lt_access.rpy').exists())

    def test_compiled_distribution_install_and_remove(self):
        bundle=self.root/'bundle';bundle.mkdir()
        shutil.copy2(SOURCE/'install_access.py',bundle/'install_access.py')
        for name in ('lt_access.rpyc','lt_access_menu.rpyc'):
            (bundle/name).write_bytes(b'compiled fixture bytes')
        command=[sys.executable,str(bundle/'install_access.py'),'--game',str(self.root)]
        result=self.run_cli(command=command)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.game/'lt_access.rpyc').read_bytes(),b'compiled fixture bytes')
        self.assertFalse((self.game/'lt_access.rpy').exists())
        self.assertEqual(self.run_cli('--uninstall',command=command).returncode,0)
        self.assertFalse((self.game/'lt_access_menu.rpyc').exists())

    def test_screen_extraction_keeps_story_code_out(self):
        source='label story:\n    "Narrative"\nscreen sample():\n    text "UI"\nlabel next_story:\n    return\n'
        blocks=m.screen_blocks(source)
        self.assertEqual(len(blocks),1)
        self.assertNotIn('label story',blocks[0])
        self.assertNotIn('next_story',blocks[0])

    def test_relationship_fields_use_labelled_editors(self):
        source='screen relation_change():\n    button:\n        id "input_mct"\n        action NullAction()\n        add Input(default=persistent.mct, changed=mc_func, length=10, button=renpy.get_widget("text_input_screen","input_mct"))\n'
        patched,_,_=m.patch_source(source,{})
        self.assertIn("alt lta_field_label('mct')",patched)
        self.assertIn("action Function(lta_open_editor, 'mct')",patched)
        self.assertNotIn('text_input_screen',patched)

    def test_context_labels_and_slider_labels(self):
        patched,_,_=m.patch_source('screen settings():\n    vbox:\n        label _("Music Volume")\n        bar value Preference("music volume")\n        textbutton _("Test") action NullAction()\n',{})
        self.assertIn('bar value Preference("music volume") alt _("Music Volume")',patched)
        self.assertIn('lta_ui_label(_("Music Volume"), _("Test"))',patched)

    def test_unvoiced_dialogue_filter_remains_in_say_window(self):
        patched,_,_=m.patch_source('screen say(who, what):\n    window:\n        text what\n',{})
        self.assertIn('alt ("" if lta_dialogue_is_voiced() else None)',patched)


if __name__=='__main__':unittest.main()
