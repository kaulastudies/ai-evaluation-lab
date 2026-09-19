class RecordTransformer:
    def transform(self, rows):
        return [
            {
                "id": row["id"],
                "value": row["value"] or None,
                "active": row["active"],
                "note": row.get("note"),
            }
            for row in rows
        ]
