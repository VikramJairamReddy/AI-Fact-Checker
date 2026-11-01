POINTS = {"true": 1, "partially_true": 0.5, "false": 0}

LABELS = {
    "true": "TRUE",
    "false": "FALSE",
    "partially_true": "PARTLY TRUE",
    "unverifiable": "COULDN'T VERIFY",
}


def truth_score(results):
    # unverifiable ones don't count either way
    scored = [r for r in results if r["verdict"] in POINTS]
    if not scored:
        return None
    total = sum(POINTS[r["verdict"]] for r in scored)
    return round(total / len(scored) * 100)


def count_verdicts(results):
    counts = {"true": 0, "partially_true": 0, "false": 0, "unverifiable": 0}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return counts


def print_report(transcript, results):
    print("\n" + "=" * 50)
    print("FACT CHECK REPORT")
    print("=" * 50)
    print("\nWhat you said:")
    print(transcript)

    if not results:
        print("\nNo factual claims found, nothing to check.")
        return

    print("\n--- Claims ---")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['claim']}")
        print("   " + LABELS[r["verdict"]] + ": " + r["explanation"])
        if r["correct_fact"]:
            print("   Truth:", r["correct_fact"])
        for s in r["sources"]:
            print("   Source:", s["title"], "-", s["url"])

    counts = count_verdicts(results)
    score = truth_score(results)

    print("\n--- Summary ---")
    print(f"Claims checked: {len(results)}")
    print(f"  true: {counts['true']}")
    print(f"  partly true: {counts['partially_true']}")
    print(f"  false: {counts['false']}")
    print(f"  couldn't verify: {counts['unverifiable']}")

    if score is None:
        print("\nTruth score: n/a (nothing could be verified)")
    else:
        print(f"\nTruth score: {score}%")


if __name__ == "__main__":
    # fake results so we can test without calling any api
    fake = [
        {"claim": "The Eiffel Tower is in Berlin", "verdict": "false",
         "explanation": "It stands in Paris.", "correct_fact": "The Eiffel Tower is in Paris, France.",
         "sources": [{"title": "Eiffel Tower", "url": "https://en.wikipedia.org/wiki/Eiffel_Tower"}]},
        {"claim": "The Eiffel Tower was built in 1889", "verdict": "true",
         "explanation": "Construction finished in 1889.", "correct_fact": "", "sources": []},
        {"claim": "Water boils at 100 C at sea level", "verdict": "true",
         "explanation": "Matches the standard boiling point.", "correct_fact": "", "sources": []},
        {"claim": "Some obscure claim", "verdict": "unverifiable",
         "explanation": "No evidence found.", "correct_fact": "", "sources": []},
    ]
    print_report("test transcript", fake)