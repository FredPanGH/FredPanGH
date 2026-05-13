"""Tests for the mortality model."""

from life_pricing.mortality import MakehamParameters, MortalityTable


def test_q_is_increasing_in_age():
    table = MortalityTable()
    qs = [table.q(age) for age in range(20, 90, 5)]
    assert all(b > a for a, b in zip(qs, qs[1:])), qs


def test_q_in_unit_interval():
    table = MortalityTable()
    for age in range(0, 119):
        q = table.q(age)
        assert 0.0 < q < 1.0, (age, q)


def test_q_at_max_age_is_one():
    table = MortalityTable(max_age=120)
    assert table.q(120) == 1.0
    assert table.q(150) == 1.0


def test_female_lower_than_male():
    table = MortalityTable()
    for age in (25, 45, 65, 85):
        assert table.q(age, gender="F") < table.q(age, gender="M")


def test_smoker_higher_than_nonsmoker():
    table = MortalityTable()
    for age in (25, 45, 65, 85):
        assert table.q(age, smoker=True) > table.q(age, smoker=False)


def test_custom_table_overrides_makeham():
    custom = {40: 0.10}
    table = MortalityTable(table=custom)
    assert abs(table.q(40) - 0.10) < 1e-12
    assert table.q(41) != 0.10


def test_survival_curve_monotone_and_starts_at_one():
    table = MortalityTable()
    curve = table.survival_curve(start_age=30, years=30)
    assert curve[0] == 1.0
    assert all(b <= a for a, b in zip(curve, curve[1:]))
    assert curve[-1] > 0.0


def test_makeham_parameters_positive():
    p = MakehamParameters()
    assert p.A > 0 and p.B > 0 and p.c > 1
