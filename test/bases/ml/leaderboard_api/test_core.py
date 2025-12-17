from ml.leaderboard_api import core


def test_app_exists():
    """Test that the FastAPI app exists."""
    assert core.app is not None
    assert core.app.title == "ml Leaderboard API"

