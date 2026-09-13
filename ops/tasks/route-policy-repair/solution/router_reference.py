DETERMINISTIC_TYPES = {"arithmetic", "regex", "schema_validation"}

def _decision(task, position, route, reason_code):
    return {
        "id": task["id"],
        "position": position,
        "route": route,
        "reason_code": reason_code,
        "policy_version": "R1",
    }

def route_batch(tasks):
    results = []

    for position, task in enumerate(tasks):
        privacy = task["privacy"]
        task_type = task["task_type"]
        confidence = float(task["local_confidence"])
        local_available = bool(task["local_available"])
        cloud_available = bool(task["cloud_available"])

        if privacy in {"confidential", "restricted"}:
            if local_available and confidence >= 0.65:
                results.append(_decision(task, position, "local", "SENSITIVE_LOCAL"))
            else:
                results.append(_decision(task, position, "blocked", "SENSITIVE_BLOCKED"))
            continue

        if task_type in DETERMINISTIC_TYPES:
            if local_available:
                results.append(_decision(task, position, "local", "DETERMINISTIC_LOCAL"))
            else:
                results.append(_decision(task, position, "blocked", "DETERMINISTIC_BLOCKED"))
            continue

        if local_available and confidence >= 0.80:
            results.append(_decision(task, position, "local", "PUBLIC_LOCAL_CONFIDENT"))
        elif cloud_available:
            results.append(_decision(task, position, "cloud", "PUBLIC_CLOUD_ESCALATION"))
        elif local_available:
            results.append(_decision(task, position, "local", "PUBLIC_LOCAL_FALLBACK"))
        else:
            results.append(_decision(task, position, "blocked", "NO_PROVIDER"))

    return results
