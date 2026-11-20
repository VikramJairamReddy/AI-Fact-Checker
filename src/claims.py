from src.llm import ask_json

PROMPT = """Pull out the factual claims from the NEW SPEECH below.

- only keep things that can be checked as true or false (dates, numbers, events, science, history, statements about people or companies)
- skip opinions, predictions, questions, greetings and filler
- make every claim stand alone: swap "he"/"it"/"they"/"that" for the real subject
- use EARLIER SPEECH only to work out what pronouns refer to, never extract claims from it
- split sentences with several facts into separate claims
- don't judge or fix the claims, just extract them

Reply with JSON only: {"claims": ["claim one", "claim two"]}
If there are none, reply {"claims": []}"""


def extract_claims(new_text, context=""):
    if not new_text.strip():
        return []
    msg = f"EARLIER SPEECH:\n{context or '(none)'}\n\nNEW SPEECH:\n{new_text}"
    data = ask_json(PROMPT, msg)
    claims = data.get("claims", [])
    return [c.strip() for c in claims if isinstance(c, str) and c.strip()]


if __name__ == "__main__":
    ctx = "I started working at Google back then."
    new = "It was in 1995 and the company had about ten thousand employees."
    for i, c in enumerate(extract_claims(new, ctx), 1):
        print(i, c)