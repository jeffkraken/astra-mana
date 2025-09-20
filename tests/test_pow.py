from astra_mana.pow import difficulty_for_hours

def test_difficulty():
    assert difficulty_for_hours(0.5) == 1
    assert difficulty_for_hours(2) == 2
    assert difficulty_for_hours(5) == 3
    assert difficulty_for_hours(12) == 4
