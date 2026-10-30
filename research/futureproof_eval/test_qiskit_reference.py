"""Independent ideal-state cross-check; no sampling calibration is claimed."""
import math
import unittest

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from research.futureproof_eval.qproof_audit import analyze
from research.futureproof_eval.verifier import born_probability, evaluate


class QiskitReferenceTests(unittest.TestCase):
    def test_analytic_reference_matches_qiskit_statevector(self):
        for theta in (-2*math.pi, -math.pi, -math.pi/2, -0.1, 0, 0.1,
                      math.pi/6, math.pi/2, math.pi, 2*math.pi):
            with self.subTest(theta=theta):
                circuit = QuantumCircuit(1)
                circuit.ry(theta, 0)
                independent = float(Statevector.from_instruction(circuit).probabilities()[1])
                self.assertAlmostEqual(born_probability(theta), independent, places=14)
                report = analyze({"id": "ideal", "theta_radians": theta,
                                  "ones": round(independent*100000), "shots": 100000})
                self.assertAlmostEqual(report['expected_p1'], independent, places=7)

    def test_reference_rejects_boolean_and_unrepresentable_numbers(self):
        for theta in (True, 10**400):
            with self.subTest(theta=repr(theta)), self.assertRaises(ValueError):
                born_probability(theta)
        for tolerance in (True, float('nan'), float('inf'), 10**400):
            with self.subTest(tolerance=repr(tolerance)), self.assertRaises(ValueError):
                evaluate('x', 0, 0, 100, tolerance)
