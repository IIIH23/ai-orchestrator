import json
from pathlib import Path

import pytest

from tools import wiki_layer


def workspace(tmp_path: Path) -> tuple[wiki_layer.WikiPaths, Path]:
    paths = wiki_layer.WikiPaths(tmp_path / "knowledge")
    wiki_layer.initialize(paths)
    source = paths.raw / "architecture-notes.md"
    source.write_text(
        "# Runtime Architecture\n\n"
        "The orchestrator uses explicit approval boundaries.\n\n"
        "Rollback evidence is retained for every deployment.\n",
        encoding="utf-8",
    )
    return paths, source


def test_initialize_creates_three_layer_structure(tmp_path: Path) -> None:
    paths = wiki_layer.WikiPaths(tmp_path / "knowledge")

    wiki_layer.initialize(paths)

    assert paths.raw.is_dir()
    assert paths.pages.is_dir()
    assert paths.schema.is_file()
    assert paths.index.is_file()
    assert paths.log.is_file()
    assert json.loads(paths.manifest.read_text(encoding="utf-8"))["sources"] == {}


def test_ingest_compiles_page_and_updates_bookkeeping(tmp_path: Path) -> None:
    paths, source = workspace(tmp_path)

    result = wiki_layer.ingest(paths, [source])

    assert result == {"ingested": ["architecture-notes.md"], "skipped": []}
    manifest = wiki_layer.load_manifest(paths)
    record = manifest["sources"]["architecture-notes.md"]
    page = paths.root / record["wiki_page"]
    page_text = page.read_text(encoding="utf-8")
    assert "status: draft" in page_text
    assert record["sha256"] in page_text
    assert "Runtime Architecture" in paths.index.read_text(encoding="utf-8")
    assert "ingest | architecture-notes.md" in paths.log.read_text(encoding="utf-8")


def test_reingest_is_idempotent(tmp_path: Path) -> None:
    paths, source = workspace(tmp_path)
    wiki_layer.ingest(paths, [source])
    original_log = paths.log.read_text(encoding="utf-8")

    result = wiki_layer.ingest(paths, [source])

    assert result == {"ingested": [], "skipped": ["architecture-notes.md"]}
    assert paths.log.read_text(encoding="utf-8") == original_log
    assert len(list(paths.pages.glob("*.md"))) == 1


def test_ingest_rejects_mutated_raw_source(tmp_path: Path) -> None:
    paths, source = workspace(tmp_path)
    wiki_layer.ingest(paths, [source])
    source.write_text("mutated", encoding="utf-8")

    with pytest.raises(wiki_layer.ImmutableSourceError, match="changed after ingest"):
        wiki_layer.ingest(paths, [source])


def test_query_reads_compiled_pages(tmp_path: Path) -> None:
    paths, source = workspace(tmp_path)
    wiki_layer.ingest(paths, [source])

    results = wiki_layer.query(paths, "rollback approval", top=3)

    assert len(results) == 1
    assert results[0]["title"] == "Runtime Architecture"
    assert "rollback" in results[0]["excerpt"].casefold()


def test_lint_detects_mutation_uningested_source_and_broken_link(tmp_path: Path) -> None:
    paths, source = workspace(tmp_path)
    wiki_layer.ingest(paths, [source])
    source.write_text("mutated", encoding="utf-8")
    (paths.raw / "new-source.txt").write_text("new", encoding="utf-8")
    page = next(paths.pages.glob("*.md"))
    page.write_text(
        page.read_text(encoding="utf-8") + "\n[[Missing Topic]]\n",
        encoding="utf-8",
    )

    result = wiki_layer.lint(paths)

    assert "immutable raw source changed: architecture-notes.md" in result["errors"]
    assert "raw source not ingested: new-source.txt" in result["warnings"]
    assert any("unresolved wikilink" in warning for warning in result["warnings"])


def test_stats_reports_measured_corpus_ratio(tmp_path: Path) -> None:
    paths, source = workspace(tmp_path)
    wiki_layer.ingest(paths, [source])

    result = wiki_layer.stats(paths)

    assert result["raw_files"] == 1
    assert result["wiki_pages"] == 1
    assert result["estimated_raw_tokens"] > 0
    assert result["estimated_wiki_tokens"] > 0
    assert result["compiled_to_raw_ratio"] is not None
    assert "not guaranteed" in result["note"]
