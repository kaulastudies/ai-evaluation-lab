# Application asset sources

These sources reproduce the strengthened application content. They do not change Lab evaluation behavior. Final PDF/PPTX files are supplied privately to the founder for manual upload.

- `content.json`: 18-slide pitch and five supporting PDF documents; the application guide follows fields 1-26.
- `build_deck.mjs`: edits an existing PPTX through ArtifactTool, reuses its 18-or-fewer source slides, appends any needed slides, and validates editable charts/tables.
- `build_documents.py`: ReportLab selectable-text PDF generator.

Use an isolated output/build workspace. The presentation builder requires the provided Codex ArtifactTool runtime and presentation validator. It will not overwrite an existing final PPTX. Set the runtime module path with a node_modules symlink in that isolated build directory, never in this repository. Run:

```bash
node build_deck.mjs /absolute/path/source.pptx content.json /absolute/path/workspace
python build_documents.py content.json /absolute/path/output
```

Create workspace/build and workspace/output before running. The source deck must have no more slides than the revised content. Export the finalized PPTX to PDF with LibreOffice or the target presentation app. Review every rendered page. Source URLs are in slide notes and the accompanying diligence brief.

Set `APPLICATION_CONTACT` privately when generating contact-bearing PDFs. Do not commit personal records, private buyer evidence, bank statements or completed financial reconciliation. The blank CSV reconciliation template is intentionally unknown throughout.

The financial model in programs/startup-qatar remains the arithmetic source. If assumptions change, regenerate its output and deliberately refresh the asset content. Validate both source numbers and rendered pages before handoff. Current assets show one initial $12,000 request; follow-on amounts are unset; $100,000 is a separate stress sensitivity.
