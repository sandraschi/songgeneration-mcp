"""Unit tests for SG2 lyric normalization."""

from songgeneration_mcp.sg2 import normalize_sg2_english_before_semicolons


def test_normalize_appends_period_before_semicolon():
    raw = "[verse] The strings arise in the Konzerthaus hall ; [chorus] Sing"
    fixed, notes = normalize_sg2_english_before_semicolons(raw, auto_fix=True)
    assert "hall." in fixed
    assert ";" in fixed or ";" in fixed.replace(" ", "")
    assert notes


def test_no_change_when_period_present():
    raw = "[verse] Hello world. ; [chorus] Next"
    fixed, notes = normalize_sg2_english_before_semicolons(raw, auto_fix=True)
    assert "Hello world." in fixed
    assert "[chorus]" in fixed
    assert not notes
