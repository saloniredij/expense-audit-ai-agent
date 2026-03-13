import pytest
from src.agent.nodes import pre_process_transactions

def test_pre_process_transactions_groups_merchants():
    state = {
        "transactions": [
            {"merchant_name": "Netflix", "amount": 15.99, "date": "2023-01-01"},
            {"merchant_name": "NETFLIX", "amount": 15.99, "date": "2023-02-01"},
            {"merchant_name": "Spotify", "amount": 9.99, "date": "2023-01-15"},
            {"merchant_name": "Coffee Shop", "amount": 4.50, "date": "2023-01-20"} # Only 1 transaction, should be ignored
        ]
    }
    
    result = pre_process_transactions(state)
    frequencies = result["merchant_frequencies"]
    
    assert "NETFLIX" in frequencies
    assert frequencies["NETFLIX"]["count"] == 2
    assert frequencies["NETFLIX"]["total_amount"] == 31.98
    assert frequencies["NETFLIX"]["avg_amount"] == 15.99
    
    # Spotify has only 1 transaction, so it is filtered out by the deterministic logic
    # Wait, the logic says > 1 transaction. So Spotify and Coffee Shop are excluded.
    assert "SPOTIFY" not in frequencies
    assert "COFFEE SHOP" not in frequencies

def test_empty_transactions():
    result = pre_process_transactions({"transactions": []})
    assert result["merchant_frequencies"] == {}
