import unittest
from eval_lab.tasks import EvaluationTask
from eval_lab.verifier import verify

class VerifierTests(unittest.TestCase):
    def test_clean_pass(self):
        t=EvaluationTask(task_id="T",version="1",prompt="",expected_behavior="",must_contain=["Paris"],mock_response="Paris")
        self.assertEqual(verify(t,"Paris").label,"PASS")
    def test_format_defect(self):
        t=EvaluationTask(task_id="T",version="1",prompt="",expected_behavior="",expected_format="json",mock_response="status: ready")
        self.assertEqual(verify(t,"status: ready").label,"NEEDS_EDIT")
    def test_prohibited_content(self):
        t=EvaluationTask(task_id="T",version="1",prompt="",expected_behavior="",must_not_contain=["APPROVED"],mock_response="APPROVED")
        self.assertEqual(verify(t,"APPROVED").label,"FAIL")
if __name__=="__main__": unittest.main()
