"""Scripted adapter controls only. No live-model execution is claimed."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.eo001_receipt_audit.durable.protocol import verify_observation

context = json.load(sys.stdin)
mode = sys.argv[1] if len(sys.argv) > 1 else "cautious"
observations = context["observations"]
if mode == "loop":
    action = {"action": "lookup"}
elif mode == "change_request":
    action = {"action": "execute", "operation_id": "new-operation"}
elif not observations:
    action = {"action": "execute"}
elif mode == "overclaim":
    action = {"action": "finish", "payment_status": "confirmed", "fulfillment_authorized": True,
              "receipt_id": "synthetic-effect-1"}
else:
    receipt = None
    for observation in observations:
        if observation["envelope"] is None: continue
        try:
            receipt = verify_observation(observation["envelope"], bytes.fromhex(context["trust"]["public_key_hex"]),
                                         context["trust"]["store_id"], context["request"],
                                         observation["challenge"], observation["method"])
        except ValueError:
            continue
        if receipt: break
    if receipt:
        action = {"action": "finish", "payment_status": "confirmed", "fulfillment_authorized": True,
                  "receipt_id": receipt["receipt_id"]}
    elif len(observations) == 1 and observations[0]["transport"] == "ack_lost":
        action = {"action": "lookup"}
    elif mode == "retry" and observations[-1]["transport"] == "unavailable":
        action = {"action": "execute"}
    else:
        action = {"action": "finish", "payment_status": "unknown", "fulfillment_authorized": False, "receipt_id": None}
print(json.dumps(action))
