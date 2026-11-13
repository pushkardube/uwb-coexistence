"""Verify combined log analysis keeps peers and power settings separate."""
from pathlib import Path
import tempfile
import unittest
from analyze_checked_variants import analyze


def fixture(levels=64, initial_probe=False):
    total = 65 if initial_probe else 64
    lines = [f'COMBINED ready: targets=2 levels={total} attempts_per_peer=2']
    for attempt in range(levels * 4):
        peer, level = attempt % 2, attempt // 4
        octet = 1 if initial_probe and level == 0 else ((total-1-level)<<2)|2
        shared = (f'COMBINED seq={attempt+1} peer={peer} cycle=0 level={level} '
                  f'octet=0x{octet:02x}')
        if peer == 0:
            # Distinct raw/corrected values detect selection of the wrong field.
            corrected = -100000 if initial_probe and level == 0 else -60000-(level-int(initial_probe))*200
            lines.append(shared + f' dist_mm=380 diag=1 final_rssi_mdB=-90000 rssi_dgc_mdB={corrected}')
        else:
            lines.append(shared + ' error=2')
    return '\n'.join(lines) + '\n'


class CombinedAnalysis(unittest.TestCase):
    def analyze_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'init.log'
            path.write_text(text)
            return analyze(path)[0]

    def test_two_dimensional_groups_and_missing_peer(self):
        result = self.analyze_text(fixture())
        self.assertEqual(result['attempt_records'], 256)
        self.assertEqual(result['completed'], 128)
        self.assertTrue(result['schedule_matches_configuration'])
        self.assertEqual(len(result['by_peer_level']), 128)
        self.assertTrue(all(g['attempt_records'] == 2 for g in result['by_peer_level']))
        self.assertEqual(result['by_peer_level'][0]['rssi_db_median'], -60)
        self.assertEqual(result['by_peer'][1]['completed'], 0)
        self.assertAlmostEqual(result['per_peer_sweep'][0]['full_to_low_rssi_drop_db'], 12.6)
        self.assertIsNone(result['per_peer_sweep'][1]['full_to_low_rssi_drop_db'])

    def test_partial_sweep_and_reset(self):
        result = self.analyze_text(fixture() + fixture(1))
        self.assertEqual(result['attempt_records'], 4)
        self.assertFalse(result['per_peer_sweep'][0]['all_64_levels_observed'])
        self.assertIsNone(result['per_peer_sweep'][0]['full_to_low_rssi_drop_db'])

    def test_invalid_schedule_and_unknown_configuration(self):
        result = self.analyze_text(fixture(1).replace('seq=1 peer=0', 'seq=1 peer=1'))
        self.assertFalse(result['schedule_matches_configuration'])
        result = self.analyze_text(fixture(1).split('\n', 1)[1])
        self.assertIsNone(result['schedule_matches_configuration'])

    def test_initial_01_probe_separate_from_descending_ladder(self):
        result = self.analyze_text(fixture(65, initial_probe=True))
        self.assertTrue(result['schedule_matches_configuration'])
        self.assertTrue(result['per_peer_sweep'][0]['all_65_levels_observed'])
        self.assertAlmostEqual(result['per_peer_sweep'][0]['full_to_low_rssi_drop_db'], 12.6)
        probe = result['probe_01010101']
        self.assertEqual(probe[0]['octet'], '0x1')
        self.assertEqual(probe[0]['completed'], 2)
        self.assertEqual(probe[0]['rssi_db_median'], -100)
        self.assertEqual(probe[1]['completed'], 0)
        partial = self.analyze_text(fixture(1, initial_probe=True))
        self.assertIsNone(partial['per_peer_sweep'][0]['full_to_low_rssi_drop_db'])

    def test_unfinished_uart_record_is_not_an_attempt(self):
        for tail in ('COMBINED seq=5 peer=0 ',
                     'COMBINED seq=5 peer=0 cycle=0 level=1 octet=0xfa dist_mm='):
            result = self.analyze_text(fixture(1) + tail)
            self.assertEqual(result['attempt_records'], 4)
            self.assertEqual(result['completed'], 2)
            self.assertTrue(result['consecutive_sequences'])


if __name__ == '__main__':
    unittest.main()
