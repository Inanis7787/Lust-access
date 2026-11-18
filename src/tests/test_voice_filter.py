import ast
from pathlib import Path
import textwrap
from types import SimpleNamespace as NS
import unittest

SOURCE=Path(__file__).resolve().parents[1]


class VoiceFilterTests(unittest.TestCase):
    def test_voice_availability_and_mute_cases(self):
        source=(SOURCE/'lt_access.rpy').read_text(encoding='utf-8')
        block=source.split('init 990 python:\n',1)[1].split('\nscreen ',1)[0]
        tree=ast.parse(textwrap.dedent(block))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='lta_dialogue_is_voiced')
        state={'filename':'voice.ogg','exists':True,'mute':False,'volume':1,'broken':False}
        persistent=NS(_voice_mute=set(),_character_volume={})
        def info():
            if state['broken']:raise ValueError('invalid metadata')
            return NS(filename=state['filename'],tag='actor')
        env=dict(config=NS(has_voice=True),_get_voice_info=info,persistent=persistent,
                 renpy=NS(loadable=lambda filename,directory:state['exists']),
                 _preferences=NS(get_mute=lambda mixer:state['mute'],get_volume=lambda mixer:state['volume']))
        exec(compile(ast.Module(body=[function],type_ignores=[]),'voice_filter','exec'),env)
        check=env['lta_dialogue_is_voiced']
        cases=[('voiced',{},True),('unvoiced',{'filename':None},False),
               ('missing',{'exists':False},False),('muted mixer',{'mute':True},False),
               ('zero mixer',{'volume':0},False),('bad metadata',{'broken':True},False)]
        for name,changes,expected in cases:
            with self.subTest(name=name):
                state.update(filename='voice.ogg',exists=True,mute=False,volume=1,broken=False)
                state.update(changes)
                self.assertEqual(check(),expected)
        state.update(filename='voice.ogg',exists=True,mute=False,volume=1,broken=False)
        with self.subTest(name='muted character'):
            persistent._voice_mute.add('actor');self.assertFalse(check());persistent._voice_mute.clear()
        with self.subTest(name='zero character volume'):
            persistent._character_volume['actor']=0;self.assertFalse(check());persistent._character_volume.clear()
        with self.subTest(name='finished clip'):
            self.assertTrue(check())  # No playback-active check: same voiced line stays excluded.


if __name__=='__main__':unittest.main()
