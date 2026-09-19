class RecordTransformer:
    def transform(self, rows):
        return [
            {
                "id": row["id"],
                "value": row["value"],
                "active": row["active"],
                "note": row.get("note") or None,
            }
            for row in rows
        ]
