"""Fixed-power captures must validate without pretending they are power sweeps."""
from pathlib import Path
import tempfile
import unittest
from analyze_checked_variants import analyze


def fixture():
    text='COMBINED ready: targets=2 levels=1 attempts_per_peer=20 mode=fixed tx_power=0x01010101\n'
    for attempt in range(100):
        base=(f'COMBINED seq={attempt+1} peer={attempt%2} cycle={attempt//40} '
              'level=0 octet=0x01 ')
        text+=base+('error=2\n' if attempt%2 else
                    'dist_mm=1000 diag=1 rssi_dgc_mdB=-85000\n')
    return text


class FixedAnalysis(unittest.TestCase):
    def read(self,text):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'init.log';p.write_text(text)
            return analyze(p)[0]

    def test_fixed_schedule_and_missing_peer(self):
        r=self.read(fixture())
        self.assertTrue(r['schedule_matches_configuration'])
        self.assertEqual(r['mode'],'fixed')
        self.assertEqual(r['fixed_tx_power'],'0x01010101')
        self.assertEqual(r['per_peer_sweep'],[])
        self.assertEqual(r['by_peer'][0]['completed'],50)
        self.assertEqual(r['by_peer'][1]['completed'],0)

    def test_rejects_changed_power_and_bad_reporting_cycle(self):
        self.assertFalse(self.read(fixture().replace('octet=0x01','octet=0xfe',1))['schedule_matches_configuration'])
        self.assertFalse(self.read(fixture().replace('cycle=1','cycle=9',1))['schedule_matches_configuration'])

    def test_requires_fixed_banner_for_one_level(self):
        self.assertIsNone(self.read(fixture().replace('mode=fixed','mode=unknown'))['schedule_matches_configuration'])


if __name__=='__main__':
    unittest.main()
