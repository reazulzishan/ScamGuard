"""Real numbers for the TF-IDF and embedding explainer Shorts (same split and code as the notebook)."""
import json, re, numpy as np, pandas as pd, torch
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline, make_union
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer
R = Path.home() / "Projects/ScamGuard"; OUT = {}
h = pd.read_csv(R / "scratch/hf_split.csv"); TR = h[h.part == "train"]; assert len(TR) == 4668
SCAM = "আপনার bKash একাউন্ট ২৪ ঘণ্টার মধ্যে বন্ধ হয়ে যাবে। এখনই ভেরিফাই করতে আপনার PIN দিন।"
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[0-9০-৯]+", "0", re.sub(r"[^\w\s]", "", str(s).lower()))).strip()
union = make_union(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True),
                   TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b"))
tfidf = make_pipeline(union, LogisticRegression(C=8, max_iter=4000, class_weight="balanced")).fit(TR["text"].map(norm), TR["label"])
fu, lr = tfidf.named_steps["featureunion"], tfidf.named_steps["logisticregression"]
cv, wv = fu.transformer_list[0][1], fu.transformer_list[1][1]
names = np.concatenate([cv.get_feature_names_out(), wv.get_feature_names_out()])
x = fu.transform([norm(SCAM)]).toarray()[0]
k = list(lr.classes_).index("smish"); contrib = x * lr.coef_[k]
nz = np.nonzero(x)[0]
top = sorted(nz, key=lambda i: -contrib[i])[:6]
idf_all = np.concatenate([cv.idf_, wv.idf_])
logits = lr.decision_function(fu.transform([norm(SCAM)]))[0]
pr = tfidf.predict_proba([norm(SCAM)])[0]
OUT["tfidf"] = {"text": SCAM, "normalised": norm(SCAM), "n_features": int(len(names)), "n_active": int(len(nz)),
                "top": [{"piece": names[i], "tfidf": round(float(x[i]), 3), "idf": round(float(idf_all[i]), 2), "weight": round(float(lr.coef_[k][i]), 2),
                         "contrib": round(float(contrib[i]), 3)} for i in top],
                "sum_smish": round(float(contrib.sum()), 3), "intercept_smish": round(float(lr.intercept_[k]), 3),
                "logits": dict(zip(lr.classes_, [round(float(v), 2) for v in logits])), "proba": dict(zip(lr.classes_, [round(float(v), 3) for v in pr]))}
# e5: real similarities + classifier probability
e5 = SentenceTransformer("intfloat/multilingual-e5-base", device="mps" if torch.backends.mps.is_available() else "cpu")
others = {"another scam": "Bangladesh Bank account has been blocked. Call to reactivate: +8801713233245",
          "a promotion": "Big Sale: Dhaka electronics shop এ ৩০% discount। Shop করুন এখন!",
          "a normal chat": "How is your day?"}
V = e5.encode(["query: " + t for t in [SCAM] + list(others.values())], normalize_embeddings=True)
OUT["e5"] = {"dim": int(V.shape[1]), "first8": V[0][:8].round(3).tolist(),
             "similarity": {k_: round(float(V[0] @ V[i + 1]), 3) for i, k_ in enumerate(others)}, "others": others}
E = np.load(R / "scratch/e5_hf.npy"); trm = (h.part == "train").values
clf = LogisticRegression(C=16, max_iter=5000, class_weight="balanced").fit(E[trm], h.label[trm])
OUT["e5"]["proba"] = dict(zip(clf.classes_, [round(float(v), 3) for v in clf.predict_proba(V[:1])[0]]))
(Path(__file__).with_name("real2.json")).write_text(json.dumps(OUT, ensure_ascii=False, indent=1))
print(json.dumps(OUT, ensure_ascii=False, indent=1)[:3000])
