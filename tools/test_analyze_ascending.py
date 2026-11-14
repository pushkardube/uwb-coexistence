import tempfile
from pathlib import Path
import unittest
from analyze_checked_variants import analyze

def fixture():
    text='COMBINED ready: targets=3 levels=65 attempts_per_peer=1 order=ascending\n'
    for level in range(65):
        octet=1 if level==0 else ((level-1)<<2)|2
        for peer in range(3):
            text+=(f'COMBINED seq={level*3+peer+1} peer={peer} cycle=0 level={level} '
                   f'octet=0x{octet:02x} dist_mm={1000+peer*1000} diag=1 '
                   f'rssi_dgc_mdB={-95000+level*300}\n')
    return text

class AscendingAnalysis(unittest.TestCase):
    def read(self,text):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'init.log';p.write_text(text)
            return analyze(p)[0]
    def test_schedule_endpoints_and_trend_direction(self):
        r=self.read(fixture())
        self.assertTrue(r['schedule_matches_configuration'])
        self.assertEqual(r['sweep_order'],'ascending')
        for peer in r['per_peer_sweep']:
            self.assertTrue(peer['all_65_levels_observed'])
            self.assertTrue(peer['observed_nondecreasing_level_medians'])
            self.assertAlmostEqual(peer['full_to_low_rssi_drop_db'],18.9)
    def test_rejects_wrong_order(self):
        self.assertFalse(self.read(fixture().replace('octet=0x02','octet=0xfe',1))['schedule_matches_configuration'])
        self.assertFalse(self.read(fixture().replace(' order=ascending',''))['schedule_matches_configuration'])
if __name__=='__main__': unittest.main()
