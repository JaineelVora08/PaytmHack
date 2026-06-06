from pprint import pprint


def run_check(label, check_fn):
    print(f"\n=== {label} ===")
    try:
        result = check_fn()
        if result is not None:
            pprint(result)
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")


def test_privacy():
    from khatavaani.backend.network_intelligence.privacy import (
        add_noise,
        hash_merchant,
        k_anonymous_signal,
    )

    return {
        "hashed_merchant": hash_merchant("demo_merchant_001"),
        "noisy_count": add_noise(100),
        "k_anonymous_4": k_anonymous_signal(4),
        "k_anonymous_5": k_anonymous_signal(5),
    }


def test_broadcast():
    from khatavaani.backend.network_intelligence.broadcast import create_campaign

    return create_campaign(
        event_id="demo_event_ipl_final",
        segment_id="nearby_2km",
        language_messages={
            "en-IN": "Cold drinks offer today.",
            "hi-IN": "Aaj cold drinks offer.",
        },
    )


def test_news_client():
    from khatavaani.backend.network_intelligence.news_client import get_trends

    return get_trends(region="urban_mumbai")


def test_network():
    from khatavaani.backend.network_intelligence.network import (
        compute_pulse,
        get_active_groups,
    )

    return {
        "pulse": compute_pulse("urban_mumbai"),
        "active_groups": get_active_groups("demo_merchant_001"),
    }


if __name__ == "__main__":
    run_check("privacy.py", test_privacy)
    run_check("broadcast.py", test_broadcast)
    run_check("news_client.py", test_news_client)
    run_check("network.py", test_network)
