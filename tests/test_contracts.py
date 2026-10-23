"""Input and provenance contracts that prevent silent evaluation corruption."""
import json,sys,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from workflow import read_records,disjoint


class InputContracts(unittest.TestCase):
    def row(self):
        return dict(response_id='1',source_id='source',task='QA',gold_hall=1,risks=[.2,.8],word_counts=[4,5])
    def read(self,rows):
        content=''.join(json.dumps(row)+'\n' for row in rows)
        with patch.object(Path,'read_text',return_value=content):
            return read_records(Path('in_memory_rows.jsonl'))
    def test_duplicate_response_is_rejected(self):
        with self.assertRaises(ValueError):self.read([self.row(),self.row()])
    def test_nan_and_out_of_range_risks_are_rejected(self):
        for risk in ([float('nan')],[1.1]):
            row=self.row();row.update(risks=risk,word_counts=[4])
            with self.assertRaises(ValueError):self.read([row])
    def test_label_direction_requires_binary_hall_label(self):
        row=self.row();row['gold_hall']='support'
        with self.assertRaises(ValueError):self.read([row])
    def test_source_leakage_is_rejected(self):
        first=self.row();second=self.row();second['response_id']='2'
        with self.assertRaises(ValueError):disjoint([first],[second])
    def test_sentence_alignment_is_required(self):
        row=self.row();row['word_counts']=[4]
        with self.assertRaises(ValueError):self.read([row])


if __name__=='__main__':unittest.main()
