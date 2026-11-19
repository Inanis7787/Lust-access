import ast
from pathlib import Path
import textwrap
from types import SimpleNamespace as NS
import unittest

SOURCE=Path(__file__).resolve().parents[1]


class StoryReviewTests(unittest.TestCase):
    def setUp(self):
        self.spoken=[]
        self.mode='say'
        self.screens={'say':NS()}
        self.context=NS(_menu=False,_main_menu=False,scene_lists=NS(layers={'screens':[]}))
        self.body='Current story line.'
        self.speaker='Speaker'
        def widget(screen,name):
            if name=='what':return NS(_tts_all=lambda:self.body)
            if name=='who' and self.speaker:return NS(_tts_all=lambda:self.speaker)
            return None
        renpy=NS(get_mode=lambda:self.mode,get_screen=lambda name:self.screens.get(name),
                 context=lambda:self.context,game=NS(context=lambda:self.context),get_displayable=widget)
        self.env=dict(renpy=renpy,lta_speak=self.spoken.append)
        source=(SOURCE/'lt_access.rpy').read_text(encoding='utf-8')
        block=source.split('init 990 python:\n',1)[1].split('\nscreen ',1)[0]
        tree=ast.parse(textwrap.dedent(block))
        names={'lta_can_review_story','lta_current_story_text','lta_review_story'}
        for function in tree.body:
            if isinstance(function,ast.FunctionDef) and function.name in names:
                exec(compile(ast.Module(body=[function],type_ignores=[]),'story_review','exec'),self.env)

    def test_read_is_explicit_and_includes_speaker(self):
        self.assertTrue(self.env['lta_can_review_story']())
        self.assertEqual(self.spoken,[])
        self.env['lta_review_story']()
        self.assertEqual(self.spoken,['Speaker: Current story line.'])

    def test_arriving_line_does_not_trigger_manual_output(self):
        self.env['lta_review_story']()
        self.body='Next line.'
        self.env['lta_can_review_story']()
        self.assertEqual(self.spoken,['Speaker: Current story line.'])
        self.env['lta_review_story']()
        self.assertEqual(self.spoken[-1],'Speaker: Next line.')

    def test_narrator_without_speaker(self):
        self.speaker=None
        self.env['lta_review_story']()
        self.assertEqual(self.spoken,['Current story line.'])

    def test_menu_and_input_modes_keep_native_keys(self):
        for mode in ('menu','screen','input','with'):
            with self.subTest(mode=mode):
                self.mode=mode
                self.assertFalse(self.env['lta_can_review_story']())
                self.env['lta_review_story']()
        self.assertEqual(self.spoken,[])

    def test_overlays_do_not_intercept_navigation(self):
        for name in ('choice','input','confirm','lta_edit'):
            with self.subTest(name=name):
                self.screens[name]=NS()
                self.assertFalse(self.env['lta_can_review_story']())
                del self.screens[name]
        for overlay in (NS(screen_name=('custom',),modal=True,tag=None),NS(screen_name=('preferences',),modal=False,tag='menu')):
            self.context.scene_lists.layers['screens']=[NS(displayable=overlay)]
            self.assertFalse(self.env['lta_can_review_story']())

    def test_missing_story_screen_is_not_read(self):
        self.screens.clear()
        self.env['lta_review_story']()
        self.assertEqual(self.spoken,[])


if __name__=='__main__':unittest.main()
