from verge_voice.languages import (
    MELIA_LANGUAGES,
    UNSUPPORTED_PLANT_REQUESTS,
    filter_hints,
    melia_language_catalog,
)


def test_melia_includes_plant_priority_languages() -> None:
    for code in ("en", "hi", "ta", "ur", "bn", "mr"):
        assert code in MELIA_LANGUAGES


def test_telugu_kannada_flagged_unsupported() -> None:
    assert "te" in UNSUPPORTED_PLANT_REQUESTS
    assert "kn" in UNSUPPORTED_PLANT_REQUESTS
    assert "te" not in MELIA_LANGUAGES
    assert "kn" not in MELIA_LANGUAGES


def test_filter_hints_drops_unsupported() -> None:
    ok, skipped = filter_hints(["en", "hi", "te", "kn", "ta"])
    assert ok == ["en", "hi", "ta"]
    assert skipped == ["te", "kn"]


def test_catalog_sorted_non_empty() -> None:
    cat = melia_language_catalog()
    assert len(cat) >= 40
    assert cat[0]["code"] < cat[-1]["code"]
