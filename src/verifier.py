import requests
from ddgs import DDGS

from src.llm import ask_json

HEADERS = {"User-Agent": "ai-fact-checker/0.1 (learning project)"}

PROMPT = """You're fact-checking a claim using numbered evidence snippets.

- judge ONLY from the evidence, not from memory
- verdict must be one of: "true", "false", "partially_true", "unverifiable"
- if it's false or partially true, say what the correct fact is
- list the numbers of the snippets you used
- explanation: one or two sentences

Reply with JSON only:
{"verdict": "...", "explanation": "...", "correct_fact": "...", "evidence_used": [1, 2]}
correct_fact is "" if the claim is true or unverifiable."""


def search_wikipedia(query, limit=3):
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": limit,
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "exlimit": limit,
        "format": "json",
    }
    try:
        res = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params=params,
            headers=HEADERS,
            timeout=10,
        )
        res.raise_for_status()
        pages = res.json().get("query", {}).get("pages", {})
    except Exception as e:
        print("wikipedia failed:", e)
        return []

    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        text = (p.get("extract") or "").strip()
        if text:
            out.append({
                "title": p["title"],
                "text": text[:800],
                "url": "https://en.wikipedia.org/?curid=" + str(p["pageid"]),
            })
    return out


def search_web(query, limit=4):
    # ddg gets rate limited sometimes, so don't crash if it fails
    try:
        hits = DDGS().text(query, max_results=limit)
    except Exception as e:
        print("web search failed:", e)
        return []
    return [
        {"title": h.get("title", ""), "text": h.get("body", "")[:500], "url": h.get("href", "")}
        for h in hits
        if h.get("body")
    ]


def verify_claim(claim):
    evidence = search_wikipedia(claim) + search_web(claim)

    if not evidence:
        return {
            "claim": claim,
            "verdict": "unverifiable",
            "explanation": "couldn't find any evidence",
            "correct_fact": "",
            "sources": [],
        }

    numbered = "\n\n".join(
        f"[{i}] {e['title']}\n{e['text']}" for i, e in enumerate(evidence, 1)
    )
    data = ask_json(PROMPT, f"Claim: {claim}\n\nEvidence:\n{numbered}")

    verdict = data.get("verdict", "unverifiable")
    if verdict not in ("true", "false", "partially_true", "unverifiable"):
        verdict = "unverifiable"

    # sources come from the real search results, the model can't make up links
    used = [n for n in data.get("evidence_used", []) if isinstance(n, int)]
    sources = [
        {"title": evidence[n - 1]["title"], "url": evidence[n - 1]["url"]}
        for n in used
        if 1 <= n <= len(evidence)
    ]

    return {
        "claim": claim,
        "verdict": verdict,
        "explanation": data.get("explanation", ""),
        "correct_fact": data.get("correct_fact", ""),
        "sources": sources,
    }


if __name__ == "__main__":
    tests = [
        "The Eiffel Tower is in Berlin",
        "The Eiffel Tower was built in 1889",
        "Water boils at 100 degrees Celsius at sea level",
    ]
    for t in tests:
        res = verify_claim(t)
        print("\n" + t)
        print(res["verdict"].upper(), "-", res["explanation"])
        if res["correct_fact"]:
            print("truth:", res["correct_fact"])
        for s in res["sources"]:
            print(" ", s["title"], s["url"])