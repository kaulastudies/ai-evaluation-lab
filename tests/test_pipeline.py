import unittest
from eval_lab.pipeline import evaluate
from eval_lab.providers.mock import MockProvider
from eval_lab.tasks import EvaluationTask

class PipelineTests(unittest.TestCase):
    def test_hash(self):
        t=EvaluationTask(task_id="T",version="1",prompt="x",expected_behavior="x",must_contain=["ok"],mock_response="ok")
        r=evaluate(t,MockProvider()); self.assertEqual(r["final_status"],"ACCEPTED"); self.assertEqual(len(r["record_hash"]),64)
    def test_disagreement(self):
        t=EvaluationTask(task_id="T",version="1",prompt="x",expected_behavior="x",must_not_contain=["bad"],mock_response="bad",synthetic_review_label="PASS",synthetic_adjudication_label="FAIL",synthetic_adjudication_reason="boundary")
        r=evaluate(t,MockProvider()); self.assertTrue(r["disagreement"]); self.assertEqual(r["final_status"],"REJECTED")
if __name__=="__main__": unittest.main()
