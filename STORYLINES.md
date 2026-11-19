# ScamGuard (CS Funda) — story design (draft)

Positioning: a TECH episode. The viewer leaves understanding shortcut learning, dataset shift,
group-safe splits, Transformer fine-tuning and LLM log-prob scoring, through one real threat.
All numbers come from the final notebook run. Brands are named only as facts; no logos, no copied app UI.

## Spine: "98% in the lab. What about your phone?"
1. Cold open (0–3 s): a phone fills with SMS. One reads "Your account will be blocked in 24 hours. Verify now."
   Text on screen: "Can an AI catch this before you do?"
2. The threat, with real numbers: Bangladesh Bank, 2025: 81,423 payment-fraud cases, Tk 92.60 crore lost,
   10.7% recovered. Rafi (seller, Ep 2) gets a fake "Cash In" SMS from an ordinary 017… number.
   bKash's own rule: staff never ask for your PIN or code; 16247 is the number to verify with.
3. The data: 7,005 SMS in Bengali, English, Banglish and code-mixed (MIT). Second, separately collected
   real-world set (CC BY 4.0) kept aside, half of it LOCKED until the very end.
4. Trap 1, near-duplicates: same template, different phone number. 74 official test messages already
   appear in train. Group-safe split.
5. Model 1, TF-IDF: ~98% in the lab. Then the wild set: the score drops. Why?
6. The investigation: shortcut learning. Training scams carry a link 58% of the time; real-world ones 1.9%.
   Training taught "money = scam": real "salary credited" notices get flagged. Label definitions differ;
   even the real-world labels have noise (shown honestly).
7. Model 2, multilingual embeddings; Model 3, fine-tuned XLM-RoBERTa (real training log on screen);
   Model 4, open LLMs with the scam definition, scored by P(Yes) vs P(No) — a Bangla LLM vs a general one.
8. The locked test, used once: the final scoreboard.
9. Payoff: ScamGuard reads Nadia's and Rafi's messages live. Viewer challenge: "Which one is a scam?"
10. Honest limits + the rule that beats every model: never share an OTP or PIN.

## Reel plan (user's choice, 2026-11-19): 3 STANDALONE reels, about 2:00–2:30 each, each < 3:00
Hook rules from real IG insights (5 s avg watch, 57–100% skip) apply to every reel:
frame 1 = full-screen phone/SMS or result + 3–6 word hook; voice at 0.0 s with the most surprising real fact;
no part counter in the first 3 s (series label only at the end); never open mid-story;
visual change every <= 2 s for the first 10 s, then a new visual beat every 4–6 s; a re-hook line every ~30 s
("but here is the problem…"); one comment/share trigger per reel; end on a question.
1. "Scam or safe?" — phone with 3 SMS, viewer guesses → the threat (real Bangladesh Bank numbers) → the data
   → the near-duplicate trap → 98% in the lab… → re-hook: "then I tested it on real scams."
2. "98% in the lab. Then real scams." — opens on the drop → shortcut learning (link = scam, money = scam,
   real 'salary credited' flagged) → label noise → embeddings → fine-tuning XLM-RoBERTa (real training log).
3. "Bangla LLM vs global LLM: who catches the scam?" — opens on the two LLM verdicts on one SMS → LLM log-prob
   scoring → locked test scoreboard → Rafi's fake 'Cash In' SMS live → the rule that beats every model.
