import ast
from pathlib import Path
import textwrap
from types import SimpleNamespace as NS
import unittest

SOURCE=Path(__file__).resolve().parents[1]


def functions(name,env):
    source=(SOURCE/name).read_text(encoding='utf-8')
    block=source.split('init 991 python:\n',1)[1].split('\ntransform ',1)[0]
    tree=ast.parse(textwrap.dedent(block))
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.Import,ast.Assign)):
            exec(compile(ast.Module(body=[node],type_ignores=[]),str(SOURCE/name),'exec'),env)
    return env


class MenuLogicTests(unittest.TestCase):
    def setUp(self):
        self.speech=[];self.saved=[];self.callbacks=[]
        self.editor=NS(scope={'draft':'New value'})
        persistent=NS(mct='Original',j_rt='',m_rt='',s_rt='',b_rt='',sont='',d_rt='')
        store=NS()
        for method in ('mc_func','j_r_func','m_r_func','s_r_func','b_r_func','son_func','d_r_func'):
            setattr(store,method,lambda value,method=method:self.callbacks.append((method,value)))
        self.env=functions('lt_access_menu.rpy',dict(persistent=persistent,
            renpy=NS(store=store,get_screen=lambda name:self.editor,save_persistent=lambda:self.saved.append(True),
                     hide_screen=lambda name:None,restart_interaction=lambda:None),lta_speak=self.speech.append))

    def test_all_seven_fields_have_distinct_callbacks(self):
        fields=self.env['LTA_FIELDS']
        self.assertEqual(len(fields),7)
        self.assertEqual(len({value[1] for value in fields.values()}),7)

    def test_commit_uses_latest_editor_draft(self):
        self.env['lta_save_edit']('mct','stale text')
        self.assertEqual(self.callbacks,[('mc_func','New value')])
        self.assertEqual(self.saved,[True])

    def test_blank_and_overlength_edits_do_not_commit(self):
        for draft in ('   ','12345678901'):
            self.editor.scope['draft']=draft
            self.env['lta_save_edit']('mct','ignored')
        self.assertEqual(self.callbacks,[])
        self.assertEqual(self.saved,[])

    def test_empty_field_does_not_commit(self):
        self.editor.scope['draft']='  '
        self.env['lta_save_edit']('mct','stale')
        self.assertEqual(self.callbacks,[])
        self.assertIn('cannot be empty',self.speech[-1])

    def test_cancel_does_not_call_any_callback(self):
        self.env['lta_cancel_editor']('lta_edit')
        self.assertEqual(self.callbacks,[])
        self.assertEqual(self.saved,[])

    def test_group_navigation_wraps_and_stays_in_range(self):
        items=[('One',None,'Settings'),('Two',None,'Settings'),('Three',None,'Navigation'),('Back',None,'Back')]
        move=self.env['lta_group_position']
        self.assertEqual(move(items,0,1),2)
        self.assertEqual(move(items,0,-1),3)
        self.assertEqual(move([('One',None,'Settings')],0,1),0)
        self.assertEqual(move([],0,1),0)

    def test_announcements_include_group_position_and_current_value(self):
        self.env['lta_announce_action']([('Music Volume: 50 percent',None,'Settings')],0)
        self.assertEqual(self.speech[-1],'Settings. 1 of 1. Music Volume: 50 percent')

    def test_styling_markup_is_removed_from_context_labels(self):
        label=self.env['lta_ui_label']('{b}Music{/b}','{size=40}Test{/size}')
        self.assertEqual(label,'Music: Test')


if __name__=='__main__':unittest.main()
