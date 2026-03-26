import pytest

from src.models import TestDesignOutput
from src.postprocessor import OutputQualityError, post_process

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Three distinct items each satisfying minimum length (>= 20 chars).
# Count intentionally equals MIN_ITEMS (3) — relied on by boundary tests.
_VALID = [
    "User logs in successfully with valid email and password credentials",
    "User is redirected to their personal dashboard after successful login",
    "Login activity is recorded in the account audit log after authentication",
]

# Clean base string shared across prefix/markdown cleaning tests.
_CLEAN_BASE = "User logs in with valid email and password combination"


def _make_output(**overrides) -> TestDesignOutput:
    """Build a valid TestDesignOutput. Override individual fields as needed."""
    defaults = {
        "positive_scenarios": _VALID[:],
        "negative_scenarios": _VALID[:],
        "edge_cases": _VALID[:],
        "clarification_questions": _VALID[:],
        "risks": _VALID[:],
    }
    defaults.update(overrides)
    return TestDesignOutput(**defaults)


def _with_positives(*items: str) -> TestDesignOutput:
    """Build output with specific positive_scenarios; all other fields use _VALID."""
    return _make_output(positive_scenarios=list(items))


def _item_of_length(n: int) -> str:
    """Return a plausible scenario string of exactly n characters."""
    base = "User authenticates and accesses the protected resource successfully"
    if len(base) >= n:
        return base[:n]
    return base + " " + "x" * (n - len(base) - 1)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_valid_output_passes_through(self):
        result = post_process(_make_output())
        assert isinstance(result, TestDesignOutput)

    def test_returns_new_instance(self):
        output = _make_output()
        result = post_process(output)
        assert result is not output

    def test_all_five_fields_present(self):
        result = post_process(_make_output())
        assert result.positive_scenarios
        assert result.negative_scenarios
        assert result.edge_cases
        assert result.clarification_questions
        assert result.risks

    def test_clean_items_are_preserved(self):
        result = post_process(_make_output())
        assert result.positive_scenarios == _VALID


# ---------------------------------------------------------------------------
# Item cleaning — leading numbering
# ---------------------------------------------------------------------------


class TestCleaningLeadingNumbering:
    @pytest.mark.parametrize("prefix", [
        pytest.param("1. ", id="decimal-period"),
        pytest.param("1) ", id="decimal-paren"),
        pytest.param("- ",  id="dash"),
        pytest.param("* ",  id="asterisk"),
        pytest.param("• ",  id="bullet"),
    ])
    def test_strips_prefix(self, prefix):
        result = post_process(_with_positives(
            prefix + _CLEAN_BASE,
            _VALID[0],
            _VALID[1],
        ))
        assert result.positive_scenarios[0] == _CLEAN_BASE
        assert result.positive_scenarios[1] == _VALID[0]
        assert result.positive_scenarios[2] == _VALID[1]


# ---------------------------------------------------------------------------
# Item cleaning — inline markdown
# ---------------------------------------------------------------------------


class TestCleaningMarkdown:
    @pytest.mark.parametrize("dirty_item,expected_clean", [
        pytest.param(
            "User logs in with **valid** email and password successfully",
            "User logs in with valid email and password successfully",
            id="bold-double-asterisk",
        ),
        pytest.param(
            "User logs in with *valid* email and password successfully today",
            "User logs in with valid email and password successfully today",
            id="italic-single-asterisk",
        ),
        pytest.param(
            "Login fails when `password` field contains only whitespace characters",
            "Login fails when password field contains only whitespace characters",
            id="inline-code",
        ),
    ])
    def test_strips_markdown_syntax(self, dirty_item, expected_clean):
        result = post_process(_with_positives(dirty_item, _VALID[0], _VALID[1]))
        assert result.positive_scenarios[0] == expected_clean

    def test_collapses_internal_whitespace(self):
        result = post_process(_with_positives(
            "User  logs  in   with   valid   credentials   successfully   today",
            _VALID[0],
            _VALID[1],
        ))
        assert result.positive_scenarios[0] == "User logs in with valid credentials successfully today"


# ---------------------------------------------------------------------------
# Item length filtering — minimum
# ---------------------------------------------------------------------------


class TestMinimumItemLength:
    def test_item_at_exactly_min_length_passes(self):
        item_20 = _item_of_length(20)
        assert len(item_20) == 20
        result = post_process(_make_output(positive_scenarios=[item_20] + _VALID))
        assert item_20 in result.positive_scenarios

    def test_item_below_min_length_is_filtered(self):
        short = _item_of_length(19)
        assert len(short) == 19
        # 4 items total so filtering one still leaves MIN_ITEMS (3)
        result = post_process(_make_output(positive_scenarios=[short] + _VALID))
        assert short not in result.positive_scenarios

    def test_empty_string_is_filtered(self):
        result = post_process(_make_output(positive_scenarios=[""] + _VALID))
        assert "" not in result.positive_scenarios

    def test_whitespace_only_is_filtered(self):
        result = post_process(_make_output(positive_scenarios=["   \t  "] + _VALID))
        assert all(s.strip() for s in result.positive_scenarios)

    def test_filtering_short_items_below_minimum_raises(self):
        # All three items are too short — field drops to 0 usable items
        short = _item_of_length(10)
        with pytest.raises(OutputQualityError, match="positive_scenarios"):
            post_process(_make_output(positive_scenarios=[short, short, short]))


# ---------------------------------------------------------------------------
# Item length validation — maximum
# ---------------------------------------------------------------------------


class TestMaximumItemLength:
    def test_item_at_exactly_max_length_passes(self):
        item_300 = _item_of_length(300)
        assert len(item_300) == 300
        result = post_process(_make_output(positive_scenarios=[item_300] + _VALID))
        assert item_300 in result.positive_scenarios

    def test_item_above_max_length_raises(self):
        item_301 = _item_of_length(301)
        assert len(item_301) == 301
        with pytest.raises(OutputQualityError, match="positive_scenarios"):
            post_process(_make_output(positive_scenarios=[item_301] + _VALID))

    def test_error_message_names_field(self):
        long_item = _item_of_length(301)
        with pytest.raises(OutputQualityError, match="negative_scenarios"):
            post_process(_make_output(negative_scenarios=[long_item] + _VALID))

    def test_error_message_includes_char_count(self):
        long_item = _item_of_length(350)
        with pytest.raises(OutputQualityError, match="350"):
            post_process(_make_output(positive_scenarios=[long_item] + _VALID))


# ---------------------------------------------------------------------------
# Intra-list deduplication
# ---------------------------------------------------------------------------


class TestDeduplication:
    def test_exact_duplicate_is_removed(self):
        item = "User logs in successfully with valid email and password"
        result = post_process(_make_output(positive_scenarios=[item, item] + _VALID))
        assert result.positive_scenarios.count(item) == 1

    def test_duplicate_with_different_case_is_removed(self):
        item = "User logs in successfully with valid email and password"
        result = post_process(_make_output(positive_scenarios=[item, item.upper()] + _VALID))
        count = sum(1 for s in result.positive_scenarios if s.lower() == item.lower())
        assert count == 1

    def test_duplicate_with_trailing_punctuation_is_removed(self):
        item = "User logs in successfully with valid email and password"
        result = post_process(_make_output(positive_scenarios=[item, item + "."] + _VALID))
        assert item in result.positive_scenarios
        assert item + "." not in result.positive_scenarios

    def test_first_occurrence_is_kept(self):
        first = "User logs in successfully with valid email and password"
        duplicate = first  # exact duplicate
        result = post_process(_make_output(positive_scenarios=[first, duplicate] + _VALID))
        assert result.positive_scenarios[0] == first

    def test_distinct_items_are_both_kept(self):
        a = "User logs in successfully with correct email and password"
        b = "User is redirected to dashboard immediately after login success"
        result = post_process(_make_output(positive_scenarios=[a, b] + _VALID))
        assert a in result.positive_scenarios
        assert b in result.positive_scenarios

    def test_dedup_is_scoped_to_each_field(self):
        # Same string in two different fields — both should survive
        shared = "Session is invalidated and the user must re-authenticate again"
        result = post_process(_make_output(
            positive_scenarios=[shared] + _VALID,
            negative_scenarios=[shared] + _VALID,
        ))
        assert shared in result.positive_scenarios
        assert shared in result.negative_scenarios

    def test_duplicates_below_minimum_after_dedup_raises(self):
        # 3 identical items → dedup leaves 1 → below MIN_ITEMS (3)
        item = "User logs in successfully with valid email and password credentials"
        with pytest.raises(OutputQualityError, match="positive_scenarios"):
            post_process(_make_output(positive_scenarios=[item, item, item]))


# ---------------------------------------------------------------------------
# Field count validation
# ---------------------------------------------------------------------------


class TestFieldCountValidation:
    def test_exactly_min_items_passes(self):
        assert len(_VALID) == 3  # documents assumption about _VALID
        result = post_process(_make_output(positive_scenarios=_VALID))
        assert len(result.positive_scenarios) == 3

    def test_exactly_max_items_passes(self):
        items = [f"User action number {i} completes successfully as expected in system" for i in range(10)]
        result = post_process(_make_output(positive_scenarios=items))
        assert len(result.positive_scenarios) == 10

    def test_below_minimum_raises(self):
        with pytest.raises(OutputQualityError, match="positive_scenarios"):
            post_process(_make_output(positive_scenarios=_VALID[:2]))

    def test_above_maximum_raises(self):
        items = [f"User action number {i} completes successfully as expected in system" for i in range(11)]
        with pytest.raises(OutputQualityError, match="positive_scenarios"):
            post_process(_make_output(positive_scenarios=items))

    def test_error_message_includes_count(self):
        with pytest.raises(OutputQualityError, match="2"):
            post_process(_make_output(edge_cases=_VALID[:2]))

    def test_each_field_is_validated_independently(self):
        # Only risks is bad — error must name risks, not any other field
        with pytest.raises(OutputQualityError, match="risks"):
            post_process(_make_output(risks=_VALID[:2]))

    @pytest.mark.parametrize("field_name", [
        "positive_scenarios",
        "negative_scenarios",
        "edge_cases",
        "clarification_questions",
        "risks",
    ])
    def test_each_field_raises_when_items_too_short(self, field_name):
        short = _item_of_length(5)
        with pytest.raises(OutputQualityError, match=field_name):
            post_process(_make_output(**{field_name: [short, short, short]}))
