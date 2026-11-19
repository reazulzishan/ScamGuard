# ScamGuard — Project Report

**Author:** Reazul Akter Zishan · CS Funda (YouTube [@csfunda.official](https://www.youtube.com/@csfunda.official))
**Question:** can a model catch a scam SMS in Bangla, English and Banglish before you do — and does a great lab score survive real messages?

Every number below comes from the live, recorded run in `notebooks/01_scamguard_executed.ipynb` (2026-11-19) or from `reports/results.json`, which that run saved.

---

## 1. Why
Bangladesh Bank recorded 81,423 payment-fraud cases in 2025: Tk 92.60 crore lost, 10.7 % recovered (reported by The Daily Observer, Aug 2026; all payment fraud, not one provider). Typical scams: "your account will be blocked, verify with your PIN", fake prizes and loans, and the fake "Cash In" SMS sent to online sellers followed by "I sent it by mistake, please send it back".

## 2. Data
| Set | Size | Use | Licence |
|---|---|---|---|
| Bengali SMS Smishing Dataset (Hugging Face) | 7,005 SMS · Bengali / English / Banglish / code-mixed · normal / promo / smish | train / validation / test | MIT |
| Financial scams detection dataset — Ahmed & Islam (2025), Mendeley Data, doi:10.17632/znsk27yk3h.1 | 520 unique real messages (309 scam / 211 ham), 19 % Bangla | **real-world test only**: half open (263), half locked (257) | CC BY 4.0 |

**Trap · same template, new number.** 81 of the 1,401 official test messages were already in training once numbers are removed. Near-duplicates were grouped (character 3–5-gram cosine ≥ 0.8 → 5,495 groups) and split by group with `StratifiedGroupKFold`: train 4,668 · val 935 · test 1,402. An assert checks that no group crosses the split.

## 3. Models
| # | Model | Lab test PR-AUC | Real-world (open half) PR-AUC |
|---|---|---|---|
| 1 | TF-IDF (char 2–5 + word 1–2) + logistic regression | 0.997 | 0.923 |
| 2 | multilingual-e5-base embeddings + logistic regression | 0.997 | 0.913 |
| 3 | XLM-RoBERTa base, fine-tuned 3 epochs (278,045,955 weights, 876 steps, val macro-F1 0.991) | 0.999 | 0.904 |
| 4a | TigerLLM-1B-it, zero-shot | 0.542 | 0.814 |
| 4b | Qwen2.5-3B-Instruct, zero-shot | 0.881 | **0.978** |
Random baseline: 0.401 (lab), 0.643 (real-world open half).

The LLMs are not trained: they get a written definition of a scam, and the score is P(Yes) / (P(Yes) + P(No)) for the next token — one forward pass, no text generation.

## 4. Why the trained models dropped: shortcut learning
| Share of scam messages that… | training data | real-world set |
|---|---|---|
| contain a link | 56.0 % | 1.9 % |
| contain a phone number | 29.6 % | 0.3 % |
| mention OTP or PIN | 6.4 % | 17.2 % |
The trained models learned "link = scam" and "money = scam": real "Salary credited: 35,000 BDT…" and "Thank you for your recent bank deposit…" were flagged as scams with 0.99 confidence, while fake cashback and loan offers were missed. The two datasets also define "scam" differently (a cashback offer is *promotion* in one, *scam* in the other), and some real-world labels are noisy ("You have a new message from the lottery office. Claim winnings." is labelled safe).

## 5. Locked real-world test (257 messages, 54.5 % scams, used once)
Each model's cut-off was chosen on the open half, then applied unchanged.
| Model | PR-AUC | F1 | scams caught | false alarms |
|---|---|---|---|---|
| **Qwen2.5-3B (zero-shot)** | **0.957** | 0.876 | 88.6 % | **16.2 %** |
| XLM-RoBERTa (fine-tuned) | 0.854 | 0.751 | 82.9 % | 45.3 % |
| TF-IDF | 0.850 | 0.785 | 87.1 % | 41.9 % |
| e5 embeddings | 0.808 | 0.751 | 91.4 % | 62.4 % |
| TigerLLM-1B | 0.649 | 0.722 | 86.4 % | 63.2 % |
**The best model in the lab was not the best model in the real world.**

## 6. Inside the models (real values, `video/realviz/`)
- XLM-R tokenizer: the bKash scam SMS becomes 26 tokens; "bKash" splits into b + K + ash.
- Attention (last layer, mean of 12 heads, from the classification token) peaks on bKash, PIN, 24 and verify.
- Classification head: untrained 38.0 % normal / 26.9 % promo / 35.1 % scam → fine-tuned 99.9 % scam.
- TF-IDF on the same SMS: 174 of 74,974 features active; sum of contributions 4.36, bias −1.22, scam logit 3.14 → softmax 98.1 % scam.
- e5: cosine similarity to another scam 0.832, a promotion 0.819, a normal chat 0.775 → classifier 77.0 % scam.
- Qwen2.5-3B on "Bhai, vul kore… ferot pathan": P(Yes) 0.9998, P(No) 0.0002 (167-token prompt).

## 7. Honest limits and a bug
- The real-world set is small (520) and partly noisy; the definitions of "scam" differ between datasets.
- The fake "Cash In" SMS cannot be judged from text alone (Qwen: 0.54) — the clue is the sender, which is not in the text.
- Bug found while making the video: the text cleaner (`[^\w\s]`) dropped Bangla vowel signs ("করুন" → "করন"). Fixing it changed the real-world PR-AUC from 0.923 to 0.922 (no meaningful effect); the fix is in the product.
- Qwen2.5-3B is licensed for non-commercial research only; it is used here for evaluation.

## 8. Reproduce
```
python3.11 -m venv .venv && .venv/bin/pip install pandas pyarrow scikit-learn torch transformers sentence-transformers nbformat nbclient jupyterlab
# data/raw/hf/{train,validation,test}.parquet  ← huggingface.co/datasets/Piash2026/bengali-sms-smishing-dataset
# data/raw/mendeley/financial_scams.csv       ← data.mendeley.com/datasets/znsk27yk3h/1
cd notebooks && ../.venv/bin/python make_notebook.py      # builds 01_scamguard.ipynb
../.venv/bin/jupyter lab 01_scamguard.ipynb                # ~25 min on a 16 GB Apple-silicon Mac
```
`recording/record_run.py` re-runs it live in JupyterLab and records the screen.

## 9. Video production
`video/script.md` (narration), `video/make_vo.py` (voice), `video/film/build_sg.py` (HyperFrames scenes: real cell captures with highlight boxes, charts drawn from `reports/results.json`, real-model visuals from `video/realviz/`). Outputs: YouTube 10:27, three standalone Reels, four technical Shorts, and a full vertical Reel. Licensed media and voice audio are not redistributed.

## Credits
Bengali SMS Smishing Dataset (MIT) · Ahmed & Islam (2025), Mendeley Data, CC BY 4.0 · Models: xlm-roberta-base (MIT), intfloat/multilingual-e5-base (MIT), md-nishat-008/TigerLLM-1B-it (CC BY 4.0), Qwen/Qwen2.5-3B-Instruct (Qwen Research License) · bKash security guidance: bkash.com · Footage: Pexels · Music: Pixabay.
