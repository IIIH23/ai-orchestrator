from tools.inventory import collect_files, render_inventory


def test_collect_and_render_inventory(tmp_path):
    (tmp_path / "alpha.txt").write_text("alpha", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "bravo.json").write_text("{}", encoding="utf-8")
    (tmp_path / "excluded").mkdir()
    (tmp_path / "excluded" / "hidden.dat").write_text("hidden", encoding="utf-8")

    files = collect_files(
        tmp_path, maximum_depth=None, exclude_patterns=("excluded",)
    )
    paths = {path.as_posix() for path, _ in files}

    assert "alpha.txt" in paths
    assert "nested/bravo.json" in paths
    assert "excluded/hidden.dat" not in paths

    rendered = render_inventory(tmp_path, files)

    assert "alpha.txt" in rendered
    assert "nested/bravo.json" in rendered
