class RecordTransformer:
    def transform(self, rows):
        result = [{k: r.get(k) for k in ("id", "value", "active", "note")} for r in rows]
        for row in rows:
            row["active"] = int(row["active"])
        return result
