"""
Unit tests for the LogLens stats module.
"""

from loglens.stats import compute_stats


def test_compute_stats_counts_and_metrics():
    """Stats correctly computes totals, match rate, top IPs, and status counts."""
    rows = [
        {"ip": "1.1.1.1", "status": "200", "path": "/index.html", "time": "2025-10-10 13:55:00"},
        {"ip": "1.1.1.1", "status": "200", "path": "/index.html", "time": "2025-10-10 13:55:10"},
        {"ip": "2.2.2.2", "status": "500", "path": "/api/err", "time": "2025-10-10 13:55:20"},
        {"ip": "3.3.3.3", "status": "404", "path": "/missing", "time": "2025-10-10 13:56:00"},
        {"ip": "1.1.1.1", "status": "502", "path": "/api/down", "time": "2025-10-10 13:56:10"},
    ]
    # Total lines = 6 (5 matched, 1 unmatched)
    stats = compute_stats(rows, total_lines=6, unmatched=1)

    assert stats["total_lines"] == 6
    assert stats["matched"] == 5
    assert stats["unmatched"] == 1
    # 5 / 6 = 83.333% -> 83.3%
    assert stats["match_rate"] == 83.3

    # Top IPs
    assert stats["top_ips"][0] == ("1.1.1.1", 3)

    # Status counts sorted
    assert stats["status_counts"] == {"200": 2, "404": 1, "500": 1, "502": 1}

    # Top paths
    assert stats["top_paths"][0] == ("/index.html", 2)

    # Errors per minute: 500 at 13:55, 502 at 13:56
    assert stats["errors_per_minute"] == {
        "2025-10-10 13:55": 1,
        "2025-10-10 13:56": 1,
    }


def test_unparseable_time_does_not_crash_errors_per_minute():
    """Unparseable time values in error rows are gracefully skipped without crashing."""
    rows = [
        {"status": "500", "time": "UNPARSEABLE_TIME_STRING"},
        {"level": "ERROR", "time": "NOT_A_REAL_DATE"},
        {"status": "500", "time": "10/Oct/2025:13:55:36 +0000"},
    ]
    stats = compute_stats(rows, total_lines=3, unmatched=0)
    assert "errors_per_minute" in stats
    # Only the valid nginx timestamp was converted
    assert stats["errors_per_minute"] == {"2025-10-10 13:55": 1}


def test_syslog_timestamp_errors_per_minute():
    """Syslog timestamps (without year) use time[:12] as the minute key."""
    rows = [
        {"level": "ERROR", "time": "Oct 10 13:55:36", "message": "Disk failure"},
        {"level": "CRITICAL", "time": "Oct 10 13:55:40", "message": "Kernel panic"},
    ]
    stats = compute_stats(rows, total_lines=2, unmatched=0)
    assert stats["errors_per_minute"] == {"Oct 10 13:55": 2}


def test_empty_rows():
    """Empty row stream produces basic stats without error."""
    stats = compute_stats([], total_lines=0, unmatched=0)
    assert stats["total_lines"] == 0
    assert stats["matched"] == 0
    assert stats["unmatched"] == 0
    assert stats["match_rate"] == 0.0
