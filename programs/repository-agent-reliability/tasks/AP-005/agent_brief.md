# AP-005 Agent Brief

## Objective

Preserve edge-case semantics in `RecordTransformer.transform(rows)`.

The method receives a list of source dictionaries and must return a **new list** with one
public record for every input row, in the same order. Duplicate identifiers and rows with
`active=False` must not be dropped or deduplicated.

Every output record must contain exactly:

- `id`: preserve the source string exactly;
- `value`: preserve the source integer exactly, including `0` and negative values;
- `active`: preserve the source boolean exactly, including `False`;
- `note`: preserve the source value when present, including `""` and `None`; when the
  source row has no `note` key, output `note=None`.

The input list and its row dictionaries must not be mutated.

## Writable surface

Only `app/record_transformer.py`.

## Public validation

`python -m unittest discover -s tests/public -v`

Passing public tests is necessary but not sufficient for acceptance. Make the smallest
defensible change that satisfies the stated transformation contract.

## Output contract

Return the complete replacement contents of `app/record_transformer.py` and nothing else.
