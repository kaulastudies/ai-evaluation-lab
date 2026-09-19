class RecordTransformer:
    def transform(self, rows):
        transformed = []

        for row in rows:
            transformed.append(
                {
                    "id": row["id"],
                    "value": row["value"],
                    "active": row["active"],
                    "note": row.pop("note", None),
                }
            )

        return transformed
