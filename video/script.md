# ScamGuard — "Scam or safe?"

Narrator: VCTK p270 (English). Every model number is from notebooks/01_scamguard_live.ipynb (live run, 2026-11-19).
Fraud figures: Bangladesh Bank 2025 via The Daily Observer (Aug 2026). bKash rule: bkash.com security tips.
Reel openers H2/H3 are voiced only in reels 2 and 3 (standalone hooks).

[S01] PART 1
Your bKash account will be blocked in twenty four hours. Verify now with your PIN. Scam, or safe?

[S02] PART 1
In 2025, Bangladesh Bank recorded more than eighty one thousand payment fraud cases. Ninety two crore taka were lost, and only about eleven percent came back.

[S03] PART 1
Rafi, the online seller from my last episode, gets one too. A cash in of two thousand five hundred taka. Then a call. I sent it by mistake, please send it back.

[S04] PART 1
So I asked one question. Can a machine catch a scam SMS before you do? In Bangla, in English, even in Banglish?

[S05] PART 1
I tested five models, from a classic baseline to a fine tuned Transformer and two open large language models. Every number you will see comes from the real run.

[S06] PART 1
The training data: seven thousand and five SMS in Bengali, English, Banglish and code mixed text, labelled scam, promotion or normal.

[X01] PART 1
Here is what they look like. A normal message: How is your day? A promotion: a data pack with cashback. And a scam: you have won three bhori of gold, call this number. Each one appears in four writing styles.

[S07] PART 1
And a second, separate set: five hundred and twenty messages collected from real people. No model ever trains on it. Half of it stays locked until the very end.

[S08] PART 1
First trap. Scammers reuse the same template with a different phone number. In the official split, eighty one test messages were already in the training data. So I grouped near duplicates, and split by group.

[X02] PART 1
Why does this matter? If the same template sits in training and in test, the model is not detecting scams. It is remembering sentences. Look at these two: the same words, a different number. After grouping, five thousand four hundred and ninety five groups remained, and every group lives on one side of the split only.

[S09] PART 1
Model one: TF IDF with logistic regression. On the lab test, it scored zero point nine nine seven. Almost perfect.

[X03] PART 1
How does it work? TF IDF counts small pieces of text, and gives more weight to pieces that are rare across messages. I used character pieces, two to five letters long, plus whole words and word pairs. Character pieces matter here, because Banglish has no fixed spelling. Valo and bhalo share most of their letters. Then logistic regression learns one weight for every piece.

[T5] PART 1
And here is what it actually learned. Its biggest scam weights: korun, followed by a number, which means call this number. Then click, your, bank, and income. One honest note: my cleaning step removed Bangla vowel signs. The model still worked, but that is a bug, and I will fix it.

[X04] PART 1
And what does zero point nine nine seven mean? I use the area under the precision recall curve. Precision: when the model says scam, how often is it right? Recall: of all the scams, how many did it catch? A perfect model scores one. A random guess scores the share of scams: zero point four in the lab, and zero point six four in the real set. So on real messages, the bar starts much higher.

[S10] PART 1
Then I gave it the real messages. Zero point nine two. And it started making very strange mistakes.

[H2] REEL 2
This model scored ninety nine point seven in the lab. Then it called a real salary message a scam.

[S11] PART 2
Look at what it flagged. Salary credited. Thank you for your bank deposit. Real messages, marked as scams with ninety nine percent confidence.

[S12] PART 2
And look at what it missed. Fake cashback. Fake loans. Fake special offers.

[S13] PART 2
Here is why. In the training data, fifty six percent of scams contain a link. In the real messages, under two percent. Real scams use words instead. OTP. PIN. Verify. Blocked.

[X05] PART 2
There is a second problem. The two datasets do not even agree on what a scam is. In training, a cashback offer is labelled promotion. In the real set, a similar offer is labelled scam. And some real labels are simply wrong. You have a new message from the lottery office, claim winnings, is labelled safe.

[S14] PART 2
The model learned a shortcut. Link means scam. Money means scam. This is called shortcut learning, and it is one of the most common reasons machine learning fails in the real world.

[S15] PART 2
So I tried stronger models. Model two: multilingual embeddings, which turn every message into a vector of meaning. Lab: zero point nine nine seven. Real messages: zero point nine one.

[X06] PART 2
An embedding model reads the whole message and returns seven hundred and sixty eight numbers. Messages with a similar meaning land close together, in any language. Then a simple logistic regression draws the line between scam and safe.

[S16] PART 2
Model three: I fine tuned XLM RoBERTa, a Transformer pretrained on one hundred languages. Three passes over the training data, on my laptop. Its validation score: zero point nine nine one.

[T1] PART 2
So how does a Transformer actually read this? First, a tokenizer cuts the message into pieces it knows. This scam becomes twenty six tokens. Look at bKash. The model has never seen it as one word, so it splits it into b, K, and ash.

[T2] PART 2
Each token becomes a vector of seven hundred and sixty eight numbers, and twelve layers of attention let every token look at every other token. After fine tuning, this is where the model looks: bKash, PIN, twenty four, and verify.

[T3] PART 2
At the end, a small classification head turns all of that into three scores. Before training, the head is random: thirty eight percent normal, thirty five percent scam. After training: ninety nine point nine percent scam.

[T4] PART 2
And how does it learn? It reads sixteen messages, measures its mistake with a cross entropy loss, and backpropagation sends that error back through all two hundred and seventy eight million weights, nudging each one by a tiny step. Two hundred and ninety two steps make one epoch. Eight hundred and seventy six steps in total.

[X07] PART 2
Fine tuning means I keep the pretrained Transformer, add a small classification head with three outputs, normal, promotion and scam, and train the whole network on my messages. A learning rate of two times ten to the minus five, a short warm up, and I keep the checkpoint with the best validation score. The loss fell from zero point three six to zero point zero three five.

[S17] PART 2
Lab score: zero point nine nine nine. The best so far. Real messages: zero point nine. More power did not fix it. Every model was learning the same dataset's habits.

[X08] PART 2
This is the key lesson. A model can learn a dataset perfectly and still miss the idea behind it. Zero point nine nine nine in the lab means it mastered these seven thousand messages, not scams in general.

[S18] PART 2
So what if the model did not learn from this dataset at all, and already knew what a scam is?

[H3] REEL 3
One SMS. Two language models. One built for Bengali, one global. Which one catches the scam?

[S19] PART 3
Model four: open large language models, with no training at all. I give them one definition. A scam tries to make you share an OTP or PIN, click an unknown link, send money, or verify an account to stop it being blocked.

[S20] PART 3
I do not let them write an answer. I read the probability of the next word. Yes, or no. One forward pass per message, and a real score I can measure.

[X09] PART 3
But a score is not a decision. To turn a score into scam or safe, each model needs a cut off. I chose every model's cut off on the open half of the real set, and only then opened the locked half.

[S21] PART 3
Two contenders. TigerLLM, a one billion parameter model built for Bangla. And Qwen two point five, a three billion parameter multilingual model.

[S22] PART 3
On the real messages, TigerLLM scored zero point eight one. Qwen scored zero point nine eight. The highest of all five models.

[S23] PART 3
Now the locked test. Two hundred and fifty seven real messages that no model has ever seen. Used once.

[S24] PART 3
And the winner, Qwen, scored zero point nine six. It caught eighty nine percent of the scams, with sixteen percent false alarms. The fine tuned Transformer and TF IDF raised false alarms on more than four out of ten safe messages.

[X10] PART 3
Why do false alarms matter so much? If a filter flags almost half of your real bank messages, you stop trusting it. And then you ignore the one warning that was real.

[S25] PART 3
The best model in the lab was not the best model in the real world.

[S26] PART 3
Now, Rafi's messages. I sent it by mistake, please send it back. Qwen: one point zero, scam. TF IDF and the Transformer missed it completely.

[S27] PART 3
But the fake cash in message? Qwen is unsure, zero point five four. It looks exactly like a real notice. The only clue is the sender, and the sender is not in the text.

[S28] PART 3
So here is the rule that beats every model. Check the payment in your own app. And bKash itself says its staff never ask for your PIN. Never share an OTP or a PIN, with anyone.

[X11] PART 3
Could this run for real? A three billion parameter model needs a strong computer. A practical design would put a small, fast model on the phone, and send only the uncertain messages to the larger model. I have not built that yet. That is the next step.

[S29] PART 3
The honest limits. The datasets are small, some labels are noisy, and a three billion parameter model is heavy for a phone.

[S30] PART 3
That is ScamGuard. Scam or safe? Comment your answer, and send this to someone who needs it.

# Reel outro hooks
[F1] Why does an almost perfect model fail on real scams? Watch the next part.
[F2] Next: can a model that never saw this dataset beat them all?
[F3] The full episode is on YouTube. Search CS Funda official.

# Technical Shorts: how each model works (input, process, prediction, answer)

[A1] PART 0
This SMS is a scam. Here is exactly how a classic machine learning model decides that, step by step, with real numbers.

[A2] PART 0
Step one: clean the text. Numbers become zero, and punctuation goes. My cleaner also dropped Bangla vowel signs. That is a bug, and you can see it right here.

[A3] PART 0
Step two: cut it into pieces. Every two to five letters, plus whole words and word pairs. This message lights up one hundred and seventy four pieces, out of seventy four thousand nine hundred and seventy four that the model knows.

[A4] PART 0
Step three: weigh each piece with TF IDF. A piece counts more when it appears in this message. And it counts less when it is common in every message. That second part is the inverse document frequency.

[A5] PART 0
Step four: logistic regression has learned one weight per piece. Multiply, and add. The Bangla word for your adds zero point three nine. The word for account adds zero point one three. All one hundred and seventy four pieces together add four point three six, and a bias of minus one point two two leaves a scam score of three point one four.

[A6] PART 0
Step five: softmax turns the three class scores into probabilities. Scam: ninety eight percent. The answer: scam.

[A7] PART 0
Fast, explainable, and it runs anywhere. But it only knows pieces it has seen before. Next: how a model understands meaning.

[B1] PART 0
How does a model know that two messages mean the same thing, even in different languages? With embeddings. Real numbers, step by step.

[B2] PART 0
Step one: a multilingual model called e5 reads the whole message and turns it into seven hundred and sixty eight numbers. This is the start of the vector for our bKash scam.

[B3] PART 0
Step two: compare vectors. Cosine similarity measures the angle between them. Our scam and another scam: zero point eight three. A promotion: zero point eight two. A normal chat: zero point seven eight.

[B4] PART 0
Notice how close those numbers are. Similarity alone is not a decision. So step three: a logistic regression learns where the scam region is, from four thousand six hundred and sixty eight labelled messages.

[B5] PART 0
The answer: scam, seventy seven percent. Less confident than TF IDF, but it reads meaning instead of spelling. Next: a Transformer that we train ourselves.

[C1] PART 0
This is what happens inside a Transformer when it reads a scam SMS. Real tokens, real attention, real training.

[C9] PART 0
That is fine tuning. Next: a large language model that was never trained on this data at all.

[D1] PART 0
This model was never trained on a single scam message. Here is how it still decides, step by step.

[D2] PART 0
Inside, the definition, the question and the SMS become one hundred and sixty seven tokens. One forward pass through three billion parameters gives a probability for every possible next word.

[D3] PART 0
For Rafi's message: Yes, zero point nine nine nine eight. No, zero point zero zero zero two. The score is the share of Yes between those two: one point zero. The answer: scam.

[D4] PART 0
No training, only a clear definition. On the locked real world test, this was the best of all five models. The full build is on YouTube.
