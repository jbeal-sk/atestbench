import pytest

from code_assigner import assign_codes, MAX_CODES


class TestAssignCodesBasic:
    def test_empty_list(self):
        assert assign_codes([]) == {}

    def test_single_photo(self):
        result = assign_codes(["a.jpg"])
        assert result == {"a.jpg": "A1"}

    def test_three_photos(self):
        result = assign_codes(["a.jpg", "b.jpg", "c.jpg"])
        assert result == {"a.jpg": "A1", "b.jpg": "A2", "c.jpg": "A3"}

    def test_ten_photos_wraps_digit(self):
        names = [f"photo_{i}.jpg" for i in range(10)]
        result = assign_codes(names)
        # A1 through A9 then A0
        assert result[names[0]] == "A1"
        assert result[names[8]] == "A9"
        assert result[names[9]] == "A0"

    def test_eleven_photos_starts_b(self):
        names = [f"photo_{i}.jpg" for i in range(11)]
        result = assign_codes(names)
        assert result[names[10]] == "B1"

    def test_sequence_order(self):
        """Verify full A-series sequence: A1, A2, ..., A9, A0."""
        names = [f"p{i}.jpg" for i in range(10)]
        result = assign_codes(names)
        expected = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A0"]
        for i, name in enumerate(names):
            assert result[name] == expected[i]


class TestAssignCodesEdgeCases:
    def test_max_codes_260(self):
        names = [f"photo_{i}.jpg" for i in range(260)]
        result = assign_codes(names)
        assert len(result) == 260
        # First code
        assert result[names[0]] == "A1"
        # Last code
        assert result[names[259]] == "Z0"

    def test_exceeds_max_raises_valueerror(self):
        names = [f"photo_{i}.jpg" for i in range(261)]
        with pytest.raises(ValueError):
            assign_codes(names)

    def test_codes_are_unique(self):
        names = [f"photo_{i}.jpg" for i in range(260)]
        result = assign_codes(names)
        codes = list(result.values())
        assert len(codes) == len(set(codes))

    def test_letter_transitions(self):
        """Verify transitions between letter groups."""
        names = [f"p{i}.jpg" for i in range(30)]
        result = assign_codes(names)
        # End of A: A0 at index 9
        assert result[names[9]] == "A0"
        # Start of B: B1 at index 10
        assert result[names[10]] == "B1"
        # End of B: B0 at index 19
        assert result[names[19]] == "B0"
        # Start of C: C1 at index 20
        assert result[names[20]] == "C1"
