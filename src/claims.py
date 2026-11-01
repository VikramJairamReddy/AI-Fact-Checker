from src.llm import ask_json

PROMPT = """Pull out the factual claims from this spoken transcript.

- only keep things that can be checked as true or false (dates, numbers, events, science, history)
- skip opinions, predictions, questions, greetings and filler
- make every claim stand alone: swap "he"/"it"/"they" for the real subject
- split sentences with several facts into separate claims
- don't judge or fix the claims, just extract them

Reply with JSON only: {"claims": ["claim one", "claim two"]}
If there are none, reply {"claims": []}"""


def extract_claims(transcript):
    if not transcript.strip():
        return []
    data = ask_json(PROMPT, "Transcript:\n" + transcript)
    claims = data.get("claims", [])
    return [c.strip() for c in claims if isinstance(c, str) and c.strip()]


if __name__ == "__main__":
    sample = (
        "So I think pizza is the best food ever. Anyway, the Eiffel Tower is "
        "in Berlin and it was built in 1889. Also water boils at 100 degrees "
        "Celsius at sea level, and I'll probably go there next summer."
    )
    for i, c in enumerate(extract_claims(sample), 1):
        print(i, c)