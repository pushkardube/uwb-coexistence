"""Check same-power comparison, failed peers and incomplete sweep handling."""
import csv
import tempfile
from pathlib import Path
import unittest

from collect_three_responder_rssi import summarize


READY = 'COMBINED ready: targets=3 levels=65 attempts_per_peer=2\n'


def measurement(seq, peer, distance, rssi):
    return (f'COMBINED seq={seq} peer={peer} cycle=0 level=0 octet=0x01 '
            f'dist_mm={distance} diag=1 rssi_dgc_mdB={rssi}\n')


class ThreeResponderSummary(unittest.TestCase):
    def export(self, text):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        (directory / 'init.log').write_text(text)
        return summarize(directory), directory

    def test_complete_setting_preserves_three_peers_and_units(self):
        text = READY + ''.join(measurement(i + 1, i % 3, 1000 * (i % 3 + 1),
                                          -70000 - 1000 * (i % 3)) for i in range(6))
        result, directory = self.export(text)
        row = result['rows'][0]
        self.assertTrue(row['full_attempt_budget'])
        self.assertTrue(row['all_peers_have_valid_rssi'])
        self.assertEqual(row['peer2_distance_m_median'], 3)
        self.assertEqual(row['peer2_rssi_db_median'], -72)
        self.assertEqual(row['tx_power_hex'], '0x01010101')
        with (directory / 'rssi_by_tx_setting.csv').open() as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 1)

    def test_failed_peer_and_partial_budget_are_not_zero_rssi(self):
        text = (READY + measurement(1, 0, 1000, -70000) +
                'COMBINED seq=2 peer=1 cycle=0 level=0 octet=0x01 error=2\n')
        result, _ = self.export(text)
        row = result['rows'][0]
        self.assertFalse(row['full_attempt_budget'])
        self.assertFalse(row['all_peers_have_valid_rssi'])
        self.assertEqual(row['peer1_attempts'], 1)
        self.assertEqual(row['peer1_completed'], 0)
        self.assertEqual(row['peer1_errors'], '{"2": 1}')
        self.assertIsNone(row['peer1_rssi_db_median'])
        self.assertIsNone(row['peer2_distance_m_median'])

    def test_latest_startup_and_unavailable_diagnostics(self):
        old = READY + measurement(1, 0, 9999, -99000)
        latest = READY + measurement(1, 0, 1000, -2147483648).replace('diag=1', 'diag=0')
        result, _ = self.export(old + latest)
        row = result['rows'][0]
        self.assertEqual(row['peer0_distance_m_median'], 1)
        self.assertIsNone(row['peer0_rssi_db_median'])

    def test_rejects_wrong_target_count(self):
        with self.assertRaises(ValueError):
            self.export(READY.replace('targets=3', 'targets=2') + measurement(1, 0, 1000, -70000))


if __name__ == '__main__':
    unittest.main()
