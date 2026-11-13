"""BLE notifications can fragment or combine measurement lines arbitrarily."""
import csv
from pathlib import Path
import tempfile
import unittest
from collect_checked_ble import LineSink

READY = b'COMBINED ready: targets=1 levels=65 attempts_per_peer=20\n'
LINE = (b'COMBINED seq=1 peer=0 dist_mm=1544 diag=1 octet=0x01 '
        b'cycle=0 level=0 rssi_dgc_mdB=-89365 status=03820077\n')


class BLEFraming(unittest.TestCase):
    def test_single_byte_fragments_and_coalesced_records(self):
        with tempfile.TemporaryDirectory() as directory:
            sink = LineSink(Path(directory), quiet=True)
            for value in READY + LINE:
                sink.feed(bytes([value]), 'test', 1)
            sink.feed(LINE.replace(b'seq=1', b'seq=2') + b'BLE_STATUS dropped=0\n')
            sink.close()
            data = Path(directory, 'init.log').read_bytes()
            self.assertEqual(data, READY + LINE + LINE.replace(b'seq=1', b'seq=2') + b'BLE_STATUS dropped=0\n')
            self.assertEqual(sink.metrics['measurements'], 2)
            self.assertEqual(sink.metrics['sequence_gaps'], 0)
            with Path(directory, 'measurements.csv').open() as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(rows[0]['tx_power_hex'], '0x01010101')
            self.assertEqual(rows[0]['status'], '03820077')

    def test_disconnect_discards_partial_then_full_record_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            sink = LineSink(Path(directory), quiet=True)
            sink.feed(LINE[:23])
            sink.reset_stream()
            sink.feed(LINE)
            sink.close()
            self.assertEqual(sink.metrics['measurements'], 1)
            self.assertEqual(sink.metrics['discarded_partial_bytes'], 23)
            self.assertEqual(Path(directory, 'init.log').read_bytes(), LINE)

    def test_gaps_duplicates_and_bounded_buffer(self):
        with tempfile.TemporaryDirectory() as directory:
            sink = LineSink(Path(directory), quiet=True)
            sink.feed(READY + LINE + LINE + LINE.replace(b'seq=1', b'seq=4'))
            sink.feed(b'x' * 1100)
            self.assertLessEqual(len(sink.buffer), 1024)
            sink.feed(b'\nBLE_STATUS dropped=3\n')
            sink.close()
            self.assertEqual(sink.metrics['duplicates'], 1)
            self.assertEqual(sink.metrics['sequence_gaps'], 2)
            self.assertEqual(sink.metrics['framing_errors'], 1)
            self.assertEqual(sink.metrics['maximum_reported_queue_drops'], 3)

    def test_acknowledged_records_replay_without_duplicate_measurements(self):
        with tempfile.TemporaryDirectory() as directory:
            sink = LineSink(Path(directory), quiet=True)
            header = b'BLE_RECORD boot=abcdef01 id=17\n'
            self.assertEqual(sink.feed(header + LINE[:40]), [])
            self.assertEqual(sink.feed(LINE[40:]), [('abcdef01', 17)])
            sink.reset_stream()
            self.assertEqual(sink.feed(header + LINE), [('abcdef01', 17)])
            sink.close()
            self.assertEqual(sink.metrics['measurements'], 1)
            self.assertEqual(sink.metrics['transport_replays'], 1)


if __name__ == '__main__':
    unittest.main()
