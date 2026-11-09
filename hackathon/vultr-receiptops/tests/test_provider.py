import json
import unittest

from receiptops.provider import parse_completion


def response(content, finish_reason="stop"):
    return {"choices": [{"finish_reason": finish_reason, "message": {
        "content": content, "reasoning": "Untrusted reasoning is not executable output."}}]}


class CompletionTests(unittest.TestCase):
    def test_completed_program(self):
        program = {"plan": ["Read", "Calculate", "Report"], "code": "print('{}')"}
        self.assertEqual(parse_completion(response(json.dumps(program))), program)

    def test_incomplete_answers_never_become_programs(self):
        for content, reason in [(None, "stop"), ("", "stop"),
                                ('{"code":"print(1)"}', "length"),
                                ('{"code":"print(1)"}', "content_filter")]:
            with self.subTest(content=content, reason=reason), self.assertRaises(ValueError):
                parse_completion(response(content, reason))

    def test_nonprogram_json_is_rejected(self):
        for value in [[], {"code": ""}, {"code": 123},
                      {"code": "x" * 16385}, {"code": "print(1)", "plan": [42]}]:
            with self.subTest(value=type(value).__name__), self.assertRaises(ValueError):
                parse_completion(response(json.dumps(value)))
