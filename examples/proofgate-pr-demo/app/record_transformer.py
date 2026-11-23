class RecordTransformer:
    """Convert internal rows into a public normalized shape."""

    def transform(self, rows):
        transformed = []

        for row in rows:
            # BUG: inactive rows are treated as absent.
            if not row.get("active"):
                continue

            transformed.append(
                {
                    "id": row["id"],
                    # BUG: a legitimate zero is collapsed into None.
                    "value": row.get("value") or None,
                    "active": bool(row.get("active")),
                    # BUG: an explicit empty string is collapsed into None.
                    "note": row.get("note") or None,
                }
            )

        return transformed
