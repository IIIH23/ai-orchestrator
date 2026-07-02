# Compiled Wiki Layer

## Source and scope

This implementation follows Andrej Karpathy's April 2026 LLM Wiki idea file:

<https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>

The source describes a pattern, not a finished library and not a guaranteed
token-reduction benchmark. Its core is:

1. immutable raw sources;
2. an agent-maintained, interlinked Markdown wiki;
3. a schema describing ingest, query, and maintenance rules;
4. content-oriented `index.md` and chronological `log.md`;
5. ingest, query, and lint operations.

AI Orchestrator implements those mechanics locally and without an embedding
service. It reports corpus-size estimates so savings can be measured on actual
data rather than assumed.

## Layout

```text
knowledge/
  WIKI_SCHEMA.md          agent operating contract
  raw/                    immutable curated sources
  state/manifest.json     source hashes and provenance
  wiki/index.md           regenerated content index
  wiki/log.md             append-only operation log
  wiki/pages/             compiled Markdown pages
```

## Workflow

Initialize or repair the directory structure:

```bash
python tools/wiki_layer.py init
```

Add a source under `knowledge/raw/`, then ingest it:

```bash
python tools/wiki_layer.py ingest knowledge/raw/architecture-notes.md
```

Without explicit paths, `ingest` processes every new supported source. It hashes
each source, creates a compact draft page, updates the manifest/index, and
appends the log. Re-ingesting an unchanged source is idempotent. Changing an
ingested source is rejected; add the revision under a new filename.

Query only the compiled layer:

```bash
python tools/wiki_layer.py query "rollback approval boundaries"
python tools/wiki_layer.py --json query "rollback approval boundaries" --top 3
```

Health-check and measure the knowledge base:

```bash
python tools/wiki_layer.py lint
python tools/wiki_layer.py stats
python tools/wiki_layer.py reindex
```

`stats` estimates tokens from character counts. It is an observability metric,
not a claim that any fixed percentage will be saved.

## Agent behavior

Mechanically compiled pages are drafts. An AI maintainer should:

- read the relevant draft and cited source;
- replace extraction with a compact synthesis;
- add entity/concept/comparison pages when useful;
- preserve source path and SHA-256 provenance;
- add `[[wikilinks]]`;
- mark reviewed pages `status: curated`;
- rebuild the index and run lint;
- file durable answers back into the wiki instead of leaving them only in chat.

Normal question answering searches the wiki first and reads only returned pages.
Raw files are consulted only to verify citations or fill a documented gap.

## Security boundary

The wiki is local and Git-native, but that does not make every source safe to
commit. Source curation remains a human responsibility. Secrets and personal or
restricted data must stay outside the repository.
