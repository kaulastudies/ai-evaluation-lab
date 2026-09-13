def route_batch(tasks):
    # Intentionally incomplete starting implementation.
    results = []
    for position, task in enumerate(tasks):
        route = "cloud" if task.get("complexity") == "high" else "local"
        results.append({
            "id": task.get("id"),
            "position": position,
            "route": route,
            "reason_code": (
                "PUBLIC_CLOUD_ESCALATION"
                if route == "cloud"
                else "PUBLIC_LOCAL_CONFIDENT"
            ),
            "policy_version": "R1",
        })
    return results
