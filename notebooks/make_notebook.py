"""Builds 01_scamguard.ipynb. Each md()/code() call is one cell. Run it live; every number in the video comes from that run."""
import nbformat as nbf

C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))

md("""
# ScamGuard · Can AI catch a Bangla scam SMS?
Four models, one honest test.
1. **TF-IDF + logistic regression** (characters + words)
2. **Multilingual embeddings** (multilingual-e5-base) + logistic regression
3. **Fine-tuned XLM-RoBERTa** (Transformer, trained here)
4. **Open LLMs, zero-shot**: a Bangla LLM (TigerLLM-1B-it) vs a general multilingual LLM (Qwen2.5-3B-Instruct), scored by P(Yes) vs P(No)

Data: *Bengali SMS Smishing Dataset* (Hugging Face, MIT): 7,005 SMS in Bengali, English, Banglish and code-mixed.
*Financial scams detection dataset* (Ahmed & Islam, 2025, Mendeley Data, CC BY 4.0): separately collected real messages, used only for testing.
""")

md("## Setup")
code("""
import re, json, time, numpy as np, pandas as pd, torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline, make_union
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, average_precision_score, classification_report, precision_recall_curve
from sklearn.model_selection import StratifiedGroupKFold, GroupShuffleSplit
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.csgraph import connected_components
pd.set_option("display.width", 140); pd.set_option("display.max_colwidth", 90)
SEED = 42; np.random.seed(SEED); torch.manual_seed(SEED)
RAW, OUT = "../data/raw/", "../reports/"
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
print("device:", DEV)
""")

md("# 1 · The data")
code("""
sms = pd.concat([pd.read_parquet(RAW + f"hf/{s}.parquet") for s in ["train", "validation", "test"]], ignore_index=True)
print(sms.shape)
pd.crosstab(sms["source"], sms["label"], margins=True)
""")
code("""
# A second, separately collected set of real messages. Never used for training.
wild = pd.read_csv(RAW + "mendeley/financial_scams.csv").dropna(subset=["message"]).drop_duplicates("message").reset_index(drop=True)
bangla = wild["message"].str.contains(r"[\\u0980-\\u09FF]")
print(wild.shape, wild["label"].value_counts().to_dict(), f"Bangla: {bangla.mean():.0%}")
""")

md("# 2 · Trap: the same scam, a different phone number")
code("""
norm = lambda s: re.sub(r"\\s+", " ", re.sub(r"[0-9০-৯]+", "0", re.sub(r"[^\\w\\s]", "", str(s).lower()))).strip()
def near_dup_groups(texts, thr=0.8):
    X = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit_transform(texts.map(norm))
    S = cosine_similarity(X, dense_output=False); S.data[S.data < thr] = 0; S.eliminate_zeros()
    return connected_components(S, directed=False)[1]
sms["grp"] = near_dup_groups(sms["text"]); wild["grp"] = near_dup_groups(wild["message"])
off_train = set(sms.loc[sms.index < 5604, "text"].map(norm))   # official train + validation rows
off_test = sms.loc[sms.index >= 5604, "text"].map(norm)
print(f"official test messages already in train (after removing numbers): {off_test.isin(off_train).sum()} of {len(off_test)}")
print(f"near-duplicate groups: {sms['grp'].nunique():,} for {len(sms):,} messages")
""")
code("""
# Split by GROUP: a template is either in training or in test, never both.
sgk = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
rest, te = next(sgk.split(sms, sms["label"] + sms["source"], groups=sms["grp"]))
r = sms.iloc[rest]
tr, va = next(StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=SEED).split(r, r["label"] + r["source"], groups=r["grp"]))
sms["part"] = "test"; sms.loc[r.index[tr], "part"] = "train"; sms.loc[r.index[va], "part"] = "val"
dev, lock = next(GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=SEED).split(wild, groups=wild["grp"]))
wild["part"] = "locked"; wild.loc[dev, "part"] = "dev"
assert not set(sms[sms.part == "train"]["grp"]) & set(sms[sms.part == "test"]["grp"]), "template leak"
print(sms["part"].value_counts().to_dict(), "| wild:", wild["part"].value_counts().to_dict(), "(locked until the end)")
TR, VA, TE = [sms[sms.part == p] for p in ["train", "val", "test"]]; WD = wild[wild.part == "dev"]
y_te, y_wd = (TE["label"] == "smish").values, (WD["label"] == "scam").values
""")

md("# 3 · Model 1 · TF-IDF + logistic regression")
code("""
tfidf = make_pipeline(make_union(
    TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True),
    TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\\b\\w+\\b")),
    LogisticRegression(C=8, max_iter=4000, class_weight="balanced"))
tfidf.fit(TR["text"].map(norm), TR["label"])
print(classification_report(TE["label"], tfidf.predict(TE["text"].map(norm)), digits=3))
""")
code("""
SCORES = {}   # model -> (lab test scores, wild dev scores). PR-AUC needs no threshold, so every model is compared fairly.
def report(name, s_te, s_wd):
    SCORES[name] = (s_te, s_wd)
    print(f"{name:28s} LAB PR-AUC {average_precision_score(y_te, s_te):.3f}   |   WILD PR-AUC {average_precision_score(y_wd, s_wd):.3f}")
smish = list(tfidf.classes_).index("smish")
report("TF-IDF", tfidf.predict_proba(TE["text"].map(norm))[:, smish], tfidf.predict_proba(WD["message"].map(norm))[:, smish])
print(f"random guess: LAB {y_te.mean():.3f}   WILD {y_wd.mean():.3f}")
""")

md("# 4 · Why does it fail in the wild? Shortcut learning")
code("""
URL = r"(https?://|www\\.|\\b[\\w-]+\\.(com|org|net|xyz|top|li|ly|me|info|site|bd)\\b)"
PHONE = r"(\\+?88)?01[3-9]\\d{8}"
def cues(s):
    s = str(s); return {"has link": bool(re.search(URL, s, re.I)), "has phone": bool(re.search(PHONE, s)),
                        "mentions OTP/PIN": bool(re.search(r"otp|pin|ওটিপি|পিন", s, re.I))}
lab = pd.DataFrame(list(sms.loc[sms.label == "smish", "text"].map(cues))).mean()
real = pd.DataFrame(list(wild.loc[wild.label == "scam", "message"].map(cues))).mean()
pd.DataFrame({"training scams": lab, "real-world scams": real}).round(3)
""")
code("""
WD = WD.assign(p=SCORES["TF-IDF"][1])
print("FALSE ALARMS (safe messages flagged):"); print(WD[(WD.label == "ham") & (WD.p >= .5)].nlargest(6, "p")[["p", "message"]].round(2).to_string(index=False))
print("\\nMISSED SCAMS:"); print(WD[(WD.label == "scam") & (WD.p < .5)].nsmallest(6, "p")[["p", "message"]].round(2).to_string(index=False))
""")

md("# 5 · Model 2 · Multilingual embeddings")
code("""
from sentence_transformers import SentenceTransformer
e5 = SentenceTransformer("intfloat/multilingual-e5-base", device=DEV)
emb = lambda s: e5.encode(["query: " + x for x in s.astype(str)], batch_size=64, normalize_embeddings=True)
WL = wild[wild.part == "locked"]   # embedded now, but scored only in the locked test at the end
E_tr, E_te, E_wd, E_wl = emb(TR["text"]), emb(TE["text"]), emb(WD["message"]), emb(WL["message"])
e5_lr = LogisticRegression(C=16, max_iter=5000, class_weight="balanced").fit(E_tr, TR["label"])
k = list(e5_lr.classes_).index("smish")
report("e5 embeddings", e5_lr.predict_proba(E_te)[:, k], e5_lr.predict_proba(E_wd)[:, k])
import gc; del e5, emb; gc.collect(); torch.mps.empty_cache() if DEV == "mps" else None   # free memory for the bigger models
""")

md("# 6 · Model 3 · Fine-tune XLM-RoBERTa")
code("""
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
LAB = ["normal", "promo", "smish"]; MN = "xlm-roberta-base"
tok = AutoTokenizer.from_pretrained(MN)
xlmr = AutoModelForSequenceClassification.from_pretrained(MN, num_labels=3).to(DEV)
def batches(texts, labels=None, bs=16, shuffle=False):
    idx = np.random.permutation(len(texts)) if shuffle else np.arange(len(texts))
    for i in range(0, len(idx), bs):
        j = idx[i:i + bs]
        b = tok([str(texts[k]) for k in j], padding=True, truncation=True, max_length=128, return_tensors="pt").to(DEV)
        yield b, (torch.tensor([labels[k] for k in j]).to(DEV) if labels is not None else None)
def xlmr_probs(texts):
    xlmr.eval(); out = []
    with torch.no_grad():
        for b, _ in batches(list(texts), bs=64): out.append(torch.softmax(xlmr(**b).logits, -1).float().cpu().numpy())
    return np.concatenate(out)
""")
code("""
X, y = list(TR["text"]), [LAB.index(l) for l in TR["label"]]
EPOCHS = 3; steps = EPOCHS * int(np.ceil(len(X) / 16))
opt = torch.optim.AdamW(xlmr.parameters(), lr=2e-5, weight_decay=0.01)
sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)
best, t0 = -1, time.time()
for ep in range(EPOCHS):
    xlmr.train(); total = 0
    for step, (b, yy) in enumerate(batches(X, y, shuffle=True)):
        loss = xlmr(**b, labels=yy).loss; loss.backward()
        torch.nn.utils.clip_grad_norm_(xlmr.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad(); total += loss.item()
        if DEV == "mps" and step % 50 == 0: torch.mps.empty_cache()   # keep GPU memory flat on a 16 GB Mac
    f = f1_score(VA["label"], [LAB[i] for i in xlmr_probs(VA["text"]).argmax(1)], average="macro")
    print(f"epoch {ep + 1}  loss {total / np.ceil(len(X) / 16):.4f}  val macro-F1 {f:.4f}  ({(time.time() - t0) / 60:.1f} min)")
    if f > best: best = f; torch.save(xlmr.state_dict(), OUT + "xlmr_best.pt")
del opt, sched; gc.collect(); torch.mps.empty_cache() if DEV == "mps" else None   # optimizer state no longer needed
xlmr.load_state_dict(torch.load(OUT + "xlmr_best.pt"))
report("XLM-RoBERTa (fine-tuned)", xlmr_probs(TE["text"])[:, 2], xlmr_probs(WD["message"])[:, 2])
""")

md("# 7 · Model 4 · Open LLMs, zero-shot")
code("""
from transformers import AutoModelForCausalLM
SYSTEM = ("You are a fraud analyst for SMS and mobile banking in Bangladesh (bKash, Nagad, Rocket, banks). "
          "A message is a SCAM if it tries to make the reader act for the sender's benefit: share an OTP, PIN or password, "
          "click an unknown link, call or send money to an unknown number, pay a fee to get a prize, loan or job, "
          "or 'verify' an account to stop it being blocked. Ordinary transaction notices, OTP messages that say not to share, "
          "personal chats and genuine promotions are NOT scams.")
def llm_scorer(name):
    t = AutoTokenizer.from_pretrained(name); t.padding_side = "left"; t.pad_token = t.pad_token or t.eos_token
    m = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch.float16).to(DEV).eval()
    yes = [t.encode(w, add_special_tokens=False)[0] for w in ["Yes", " Yes", "YES"]]
    no = [t.encode(w, add_special_tokens=False)[0] for w in ["No", " No", "NO"]]
    def prompt(sms_text):
        q = f"SMS:\\n{sms_text}\\n\\nIs this SMS a scam? Answer Yes or No."
        try: return t.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}], tokenize=False, add_generation_prompt=True)
        except Exception:
            try: return t.apply_chat_template([{"role": "user", "content": SYSTEM + "\\n\\n" + q}], tokenize=False, add_generation_prompt=True)
            except Exception: return SYSTEM + "\\n\\n" + q + "\\nAnswer:"
    def score(texts, bs=8):   # P(Yes) vs P(No) for the next token: one forward pass, no text generation
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), bs):
                b = t([prompt(str(x)) for x in texts[i:i + bs]], return_tensors="pt", padding=True, add_special_tokens=False).to(DEV)
                lp = torch.log_softmax(m(**b, logits_to_keep=1).logits[:, -1, :].float(), -1)   # only the last token's logits
                out.append(torch.sigmoid(torch.logsumexp(lp[:, yes], -1) - torch.logsumexp(lp[:, no], -1)).cpu().numpy())
        return np.concatenate(out)
    return m, score
""")
code("""
LLMS = {"TigerLLM-1B (Bangla)": "md-nishat-008/TigerLLM-1B-it", "Qwen2.5-3B (multilingual)": "Qwen/Qwen2.5-3B-Instruct"}
demo = ["আপনার bKash একাউন্ট ২৪ ঘণ্টার মধ্যে বন্ধ হয়ে যাবে। এখনই ভেরিফাই করতে আপনার PIN দিন।",
        "Cash In Tk 2,500.00 from 01712XXXXXX successful. Balance Tk 2,612.40. TrxID 9KX3...",
        "Bhai, vul kore apnar number e 2500 taka pathiye felsi, please ferot pathan.",
        "আপনার OTP 482913। এটি কারো সাথে শেয়ার করবেন না।",
        "Apnar order ti aj deliver hobe. Rider call korbe."]   # written for the demo, in the style of real messages
LOCKED, DEMO = {}, {}   # locked-set scores are stored now and looked at only in the locked test
for label, name in LLMS.items():
    t0 = time.time(); m, score = llm_scorer(name)
    report(label, score(list(TE["text"])), score(list(WD["message"])))
    LOCKED[label], DEMO[label] = score(list(WL["message"])), score(demo)
    del m, score; gc.collect(); torch.mps.empty_cache() if DEV == "mps" else None   # one LLM in memory at a time
    print(f"   ({time.time() - t0:.0f} s)")
""")

md("# 8 · The locked test (used once)")
code("""
y_wl = (WL["label"] == "scam").values
# Each model's cut-off is chosen on the wild DEV half, then applied unchanged to the LOCKED half.
def best_threshold(y, s):
    P, R, T = precision_recall_curve(y, s); f = 2 * P * R / (P + R + 1e-9); return T[np.argmax(f[:-1])]
final = {"TF-IDF": tfidf.predict_proba(WL["message"].map(norm))[:, smish],
         "e5 embeddings": e5_lr.predict_proba(E_wl)[:, k],
         "XLM-RoBERTa (fine-tuned)": xlmr_probs(WL["message"])[:, 2],
         **LOCKED}
rows = []
for n, s in final.items():
    th = best_threshold(y_wd, SCORES[n][1]); hit = s >= th
    rows.append({"model": n, "PR-AUC": average_precision_score(y_wl, s), "F1": f1_score(y_wl, hit),
                 "scams caught": hit[y_wl].mean(), "false alarms": hit[~y_wl].mean()})
board = pd.DataFrame(rows).round(3).sort_values("PR-AUC", ascending=False)
print(f"LOCKED real-world test: {len(WL)} messages, {y_wl.mean():.1%} scams (random PR-AUC {y_wl.mean():.3f})")
board
""")

md("# 9 · ScamGuard reads the messages")
code("""
pd.DataFrame({"message": demo, "TF-IDF": tfidf.predict_proba(pd.Series(demo).map(norm))[:, smish],
              "XLM-R": xlmr_probs(demo)[:, 2], **{n.split(" (")[0]: v for n, v in DEMO.items()}}).round(2)
""")

md("## Save results for the video charts")
code("""
def pr(y, s, n=140):
    P, R, _ = precision_recall_curve(y, s); i = np.unique(np.linspace(0, len(P) - 1, n).astype(int))
    return {"recall": R[i].round(4).tolist(), "precision": P[i].round(4).tolist(), "ap": round(float(average_precision_score(y, s)), 3)}
json.dump({"lab": {n: pr(y_te, s[0]) for n, s in SCORES.items()}, "wild": {n: pr(y_wd, s[1]) for n, s in SCORES.items()},
           "locked": board.to_dict("records"), "base": {"lab": float(y_te.mean()), "wild": float(y_wd.mean()), "locked": float(y_wl.mean())}},
          open(OUT + "results.json", "w"))
print("saved", OUT + "results.json")
""")

nb = nbf.v4.new_notebook(); nb.cells = C
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, "01_scamguard.ipynb")
print(len(C), "cells")
