"""Inspect's provider response must be bounded before dispatching any tools."""
import asyncio
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch


@unittest.skipUnless(importlib.util.find_spec("inspect_ai"), "Inspect SDK tested by security CI")
class ToolBudgetTests(unittest.TestCase):
    def test_oversized_batch_is_rejected_before_dispatch(self):
        path = Path(__file__).resolve().parents[1] / "inspect_evals/as001_live.py"
        spec = importlib.util.spec_from_file_location("as001_security_budget", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        state = SimpleNamespace(output=SimpleNamespace(message=SimpleNamespace(tool_calls=[object()] * 10000)))
        generate = AsyncMock(return_value=state)
        with patch.object(module, "store_as", return_value=SimpleNamespace(seq=0)), patch.object(module, "call_tools", new_callable=AsyncMock) as dispatch:
            with self.assertRaisesRegex(RuntimeError, "before dispatch"):
                asyncio.run(module.bounded_tool_loop()(state, generate))
            dispatch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
