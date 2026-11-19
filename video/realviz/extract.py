"""Real numbers for the 'how the models learn' visuals. Uses the notebook's saved XLM-R checkpoint, its exact split, and its exact code."""
import json, re, numpy as np, pandas as pd, torch
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline, make_union
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM, get_linear_schedule_with_warmup
R = Path.home() / "Projects/ScamGuard"; OUT = {}
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
h = pd.read_csv(R / "scratch/hf_split.csv")            # identical to the notebook split (4668 / 935 / 1402)
TR = h[h.part == "train"]; assert len(TR) == 4668
SCAM = "আপনার bKash একাউন্ট ২৪ ঘণ্টার মধ্যে বন্ধ হয়ে যাবে। এখনই ভেরিফাই করতে আপনার PIN দিন।"
MISTAKE = "Bhai, vul kore apnar number e 2500 taka pathiye felsi, please ferot pathan."
LAB = ["normal", "promo", "smish"]

# 1. tokenizer
tok = AutoTokenizer.from_pretrained("xlm-roberta-base")
ids = tok(SCAM)["input_ids"]
OUT["tokens"] = {"text": SCAM, "pieces": tok.convert_ids_to_tokens(ids), "ids": ids}

# 2. untrained head vs fine-tuned (checkpoint saved by the notebook)
def probs(m, text):
    m.eval()
    with torch.no_grad():
        b = tok([text], return_tensors="pt").to(DEV); o = m(**b, output_attentions=True)
    return torch.softmax(o.logits, -1)[0].float().cpu().numpy(), o
torch.manual_seed(42)
base = AutoModelForSequenceClassification.from_pretrained("xlm-roberta-base", num_labels=3, attn_implementation="eager").to(DEV)
OUT["n_params"] = int(sum(p.numel() for p in base.parameters()))
pb, _ = probs(base, SCAM)
ft = AutoModelForSequenceClassification.from_pretrained("xlm-roberta-base", num_labels=3, attn_implementation="eager")
ft.load_state_dict(torch.load(R / "reports/xlmr_best.pt", map_location="cpu")); ft.to(DEV)
pa, o = probs(ft, SCAM)
OUT["before_after"] = {"labels": LAB, "before": pb.round(3).tolist(), "after": pa.round(3).tolist()}
# 3. attention: last layer, mean over heads, from the <s> (classification) token to every token
att = o.attentions[-1][0].mean(0)[0].float().cpu().numpy()
OUT["attention"] = {"pieces": OUT["tokens"]["pieces"], "cls_to_token": att.round(4).tolist(), "layers": len(o.attentions), "heads": o.attentions[-1].shape[1]}
del base, ft; torch.mps.empty_cache() if DEV == "mps" else None

# 4. the real learning-rate schedule used in the notebook
EPOCHS = 3; steps = EPOCHS * int(np.ceil(len(TR) / 16))
p = torch.nn.Parameter(torch.zeros(1)); opt = torch.optim.AdamW([p], lr=2e-5)
sch = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps); lrs = []
for _ in range(steps): lrs.append(opt.param_groups[0]["lr"]); opt.step(); sch.step()
OUT["lr"] = {"steps": steps, "per_epoch": steps // EPOCHS, "warmup": int(0.06 * steps), "lr": [round(x * 1e5, 4) for x in lrs[::4]]}

# 5. TF-IDF: retrain exactly as in the notebook, read the largest scam weights (word part)
norm = lambda s: re.sub(r"\s+", " ", re.sub(r"[0-9০-৯]+", "0", re.sub(r"[^\w\s]", "", str(s).lower()))).strip()
tfidf = make_pipeline(make_union(
    TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True),
    TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b")),
    LogisticRegression(C=8, max_iter=4000, class_weight="balanced"))
tfidf.fit(TR["text"].map(norm), TR["label"])
lr_ = tfidf.named_steps["logisticregression"]; fu = tfidf.named_steps["featureunion"]
nc = len(fu.transformer_list[0][1].get_feature_names_out())
names = np.concatenate([fu.transformer_list[0][1].get_feature_names_out(), fu.transformer_list[1][1].get_feature_names_out()])
k = list(lr_.classes_).index("smish"); w = lr_.coef_[k]
wd = pd.Series(w[nc:], index=names[nc:]).sort_values()
OUT["tfidf_words"] = {"scam": [[n, round(float(v), 2)] for n, v in wd.tail(10)[::-1].items()],
                      "not_scam": [[n, round(float(v), 2)] for n, v in wd.head(6).items()], "n_features": int(len(names))}

# 6. e5 embedding map: 2-D PCA of the real embeddings (same model and prefix as the notebook)
E = np.load(R / "scratch/e5_hf.npy"); xy = PCA(2, random_state=42).fit_transform(E)
idx = np.random.RandomState(42).choice(len(h), 1500, replace=False)
OUT["e5_map"] = {"x": xy[idx, 0].round(3).tolist(), "y": xy[idx, 1].round(3).tolist(), "label": h.label.values[idx].tolist()}

# 7. Qwen: real next-token distribution for Rafi's message, with the notebook's prompt
SYSTEM = ("You are a fraud analyst for SMS and mobile banking in Bangladesh (bKash, Nagad, Rocket, banks). "
          "A message is a SCAM if it tries to make the reader act for the sender's benefit: share an OTP, PIN or password, "
          "click an unknown link, call or send money to an unknown number, pay a fee to get a prize, loan or job, "
          "or 'verify' an account to stop it being blocked. Ordinary transaction notices, OTP messages that say not to share, "
          "personal chats and genuine promotions are NOT scams.")
qt = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
qm = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct", dtype=torch.float16).to(DEV).eval()
q = f"SMS:\n{MISTAKE}\n\nIs this SMS a scam? Answer Yes or No."
pr = qt.apply_chat_template([{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}], tokenize=False, add_generation_prompt=True)
with torch.no_grad():
    b = qt(pr, return_tensors="pt", add_special_tokens=False).to(DEV)
    pdist = torch.softmax(qm(**b, logits_to_keep=1).logits[0, -1].float(), -1)
top = torch.topk(pdist, 6)
OUT["qwen_next"] = {"message": MISTAKE, "prompt_tokens": int(b["input_ids"].shape[1]),
                    "top": [[qt.decode([int(i)]), round(float(v), 4)] for v, i in zip(top.values, top.indices)]}
(Path(__file__).with_name("real.json")).write_text(json.dumps(OUT, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in OUT.items() if k not in ("e5_map", "lr", "attention")}, ensure_ascii=False)[:2500])
print("attention top:", sorted(zip(OUT["attention"]["cls_to_token"], OUT["attention"]["pieces"]), reverse=True)[:8])
print("lr:", OUT["lr"]["steps"], OUT["lr"]["warmup"])
