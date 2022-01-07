def test_autogenerate(pytester):
    pytester.copy_example()
    result = pytester.inline_run("--test-alembic")
    result.assertoutcome(passed=4)
