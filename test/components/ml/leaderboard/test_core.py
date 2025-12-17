from ml.leaderboard import core


def test_sample():
    """Test leaderboard functionality."""
    entry1 = core.LeaderboardEntry(user_id="user1", username="user1", score=100)
    entry2 = core.LeaderboardEntry(user_id="user2", username="user2", score=200)
    
    core.add_entry(entry1)
    core.add_entry(entry2)
    
    entries = core.get_top_entries(limit=2)
    
    assert len(entries) == 2
    assert entries[0].score == 200
    assert entries[0].rank == 1

