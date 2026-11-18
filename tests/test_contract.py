import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run import make_plan,sync_checks,validate_layout,detect_layout
from workspaces import PRESETS, load_workspace, pixel_box, select_workspace
from PIL import Image,ImageDraw
from check_skills import check,REQUIRED

class ContractTests(unittest.TestCase):
    def test_skill_preflight_rejects_missing_and_empty_skills(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual(set(check([root])['missing']),set(REQUIRED))
            for name in REQUIRED:
                p=root/name/'SKILL.md';p.parent.mkdir()
                p.write_text(f'---\nname: {name}\n---\nTODO',encoding='utf-8')
            self.assertFalse(check([root])['all_pass'])
            for name in REQUIRED:
                (root/name/'SKILL.md').write_text(f'---\nname: {name}\n---\n'+('Remotion export and composition instructions. '*8),encoding='utf-8')
            self.assertTrue(check([root])['all_pass'])

    def test_click_reveal_sync_at_different_durations(self):
        layout={'timeline':{'x':0,'y':.61,'width':1,'height':.39}}
        for n in [24,120,240,1865,3600]:
            d=make_plan(n,60,1920,1080,5,n/60*5,layout,'generic')
            self.assertTrue(sync_checks(d)['click_reveal_sync_pass'])
            self.assertEqual(len(d['crew']),28);self.assertEqual(len(d['tracks']),11)
            self.assertEqual(len(d['clips']),268);self.assertEqual(len(d['commits']),132)
            self.assertGreater(min(c['at'] for c in d['clips']),0)
            self.assertLess(max(c['at'] for c in d['clips']),n-1)
            for w in d['crew']:
                self.assertTrue(w['segments']);self.assertLessEqual(w['segments'][0]['from'],0)
                self.assertGreater(w['segments'][-1]['to'],n-1)
                for s in w['segments']:
                    for point in [s['p0'],s['p1']]:self.assertGreaterEqual(point[1],618)

    def test_sync_checker_finds_false_reveal(self):
        d=make_plan(1800,60,1280,720,5,150,{'timeline':{'x':0,'y':.6,'width':1,'height':.4}},'generic')
        d['clips'][0]['at']+=4
        self.assertFalse(sync_checks(d)['click_reveal_sync_pass'])

    def test_partial_timeline_and_invalid_rectangles(self):
        validate_layout({'timeline':{'x':.04,'y':.55,'width':.70,'height':.4}})
        for r in [{'x':.7,'y':.6,'width':.7,'height':.4},
                  {'x':0,'y':float('nan'),'width':1,'height':.4},
                  {'x':0,'y':.9,'width':1,'height':.1}]:
            with self.assertRaises(ValueError):validate_layout({'timeline':r})

    def test_divider_estimator_uses_image_not_product(self):
        for y in [.48,.61,.72]:
            for tone in [30,160]:
                im=Image.new('RGB',(960,540),(tone,tone,tone));dr=ImageDraw.Draw(im)
                dr.rectangle((0,round(540*y),959,539),fill=(tone+30,)*3)
                layout,det=detect_layout([im,im.copy(),im.copy()])
                self.assertTrue(det['supported']);self.assertAlmostEqual(layout['timeline']['y'],y,delta=.006)
        flat=Image.new('RGB',(960,540),(40,40,40))
        self.assertFalse(detect_layout([flat]*3)[1]['supported'])

    def test_preview_edge_above_timeline_does_not_win(self):
        im=Image.new('RGB',(960,540),(32,33,42));dr=ImageDraw.Draw(im)
        dr.rectangle((280,54,700,275),fill=(108,120,132))
        dr.rectangle((0,297,959,539),fill=(61,64,75))
        dr.rectangle((145,390,770,442),fill=(82,132,138))
        l,d=detect_layout([im]*3)
        self.assertTrue(d['supported']);self.assertAlmostEqual(l['timeline']['y'],.55,delta=.006)

    def test_static_templates_have_separate_player_and_timeline(self):
        for name in PRESETS:
            _, image, layout = select_workspace(name, None, None)
            self.assertEqual(load_workspace(image).size, (1920,1080))
            validate_layout(layout)
            self.assertTrue(all(value % 2 == 0 for value in pixel_box(layout['player'],1920,1080)))
            with self.assertRaisesRegex(ValueError, 'overlap'):
                validate_layout(dict(layout, player=layout['timeline']))

if __name__=='__main__':unittest.main()
