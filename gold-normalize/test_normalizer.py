"""
Pure tests for Gold Canonical normalization helpers.

Run:
    python3 gold-normalize/test_normalizer.py
"""

from normalizer import (
    EntityResolver,
    normalize_aspect,
    normalize_label,
    relation_endpoint_from_review_entities,
)


def test_normalize_label():
    assert normalize_label(" Bagmati River! ") == "bagmati river"
    assert normalize_label("Pashupati-Nath Temple") == "pashupati nath temple"


def test_automatic_subset_alias_resolution():
    resolver = EntityResolver()
    resolver.add_existing("bagmati_river", "Bagmati River", "sacred_space", entity_id=7)
    resolved = resolver.resolve("Holy Bagmati River", "sacred_space")
    assert resolved.canonical_name == "bagmati_river"
    assert resolved.display_name == "Bagmati River"
    assert resolved.entity_type == "sacred_space"
    assert resolved.matched_by == "token_subset"


def test_no_static_entity_alias_mapping():
    resolver = EntityResolver()
    resolved = resolver.resolve("Holy Bagmati River", "sacred_space")
    assert resolved.canonical_name == "holy_bagmati_river"
    assert resolved.matched_by == "new"


def test_fuzzy_resolution():
    resolver = EntityResolver(auto_threshold=90)
    resolver.add_existing("pashupatinath_temple", "Pashupatinath Temple", "sacred_space")
    resolved = resolver.resolve("Pashupatinath Templ", "sacred_space")
    assert resolved.canonical_name == "pashupatinath_temple"
    assert resolved.matched_by == "fuzzy"


def test_nepal_heritage_token_equivalence():
    resolver = EntityResolver()
    resolver.add_existing("pashupatinath_temple", "Pashupatinath Temple", "sacred_space")
    resolved = resolver.resolve("Pashupatinath Mandir", "sacred_space")
    assert resolved.canonical_name == "pashupatinath_temple"
    assert resolved.matched_by == "token_equivalent"


def test_nepal_heritage_ritual_equivalence():
    resolver = EntityResolver()
    resolver.add_existing("evening_aarti", "Evening Aarti", "ritual")
    resolved = resolver.resolve("Evening Aarati", "ritual")
    assert resolved.canonical_name == "evening_aarti"
    assert resolved.matched_by == "token_equivalent"


def test_learned_alias_resolution():
    resolver = EntityResolver()
    resolver.add_existing("bagmati_river", "Bagmati River", "sacred_space", entity_id=7)
    resolver.add_alias("sacred river", "bagmati_river", "Bagmati River", "sacred_space", entity_id=7)
    resolved = resolver.resolve("Sacred River", "sacred_space")
    assert resolved.canonical_name == "bagmati_river"
    assert resolved.matched_by == "learned_alias"


def test_candidate_resolution_does_not_merge():
    resolver = EntityResolver(auto_threshold=100, candidate_threshold=90)
    resolver.add_existing("pashupatinath_temple", "Pashupatinath Temple", "sacred_space", entity_id=3)
    resolved = resolver.resolve("Pashupatinath Templ", "sacred_space")
    assert resolved.is_candidate is True
    assert resolved.canonical_name == "pashupatinath_templ"
    assert resolved.suggested_canonical_name == "pashupatinath_temple"


def test_relation_endpoint_numeric_fallback():
    review_entities = [
        {"id": 10, "entity_name": "Darshan", "entity_type": "ritual"},
        {"id": 11, "entity_name": "Inner Peace", "entity_type": "spiritual_emotion"},
    ]
    resolved = relation_endpoint_from_review_entities("2", review_entities)
    assert resolved["entity_name"] == "Inner Peace"
    assert resolved["entity_type"] == "spiritual_emotion"


def test_aspect_normalization():
    resolved = normalize_aspect("Ritual Experience")
    assert resolved.aspect == "ritual_experience"
    assert resolved.display_aspect == "Ritual Experience"


def main():
    tests = [
        test_normalize_label,
        test_automatic_subset_alias_resolution,
        test_no_static_entity_alias_mapping,
        test_fuzzy_resolution,
        test_nepal_heritage_token_equivalence,
        test_nepal_heritage_ritual_equivalence,
        test_learned_alias_resolution,
        test_candidate_resolution_does_not_merge,
        test_relation_endpoint_numeric_fallback,
        test_aspect_normalization,
    ]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} normalizer tests")


if __name__ == "__main__":
    main()
