class RecordTransformer:
    """Convert internal rows into a public normalized shape."""

    def transform(self, rows):
        transformed = []

        for row in rows:
            transformed.append(
                {
                    "id": row["id"],
                    "value": row["value"],
                    "active": row["active"],
                    "note": row.get("note"),
                }
            )

        return transformed
