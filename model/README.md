📚 Ye FOLDER se ek NAYA AI MODEL paida ho raha hai — bilkul offline, bina kisi API key ke.

Project name: Hemomemo AI (Generation One)
Birthplace : D:/DigitalBrain
Technology : Pure NumPy neural network (LSTM char-level language model)
Policy     : ZERO external API, ZERO cloud — sab kuch is folder ke andar

Files:
  model/nn.py          → LSTM brain cells (numpy se bane)
  model/tokenizer.py   → text ↔ vocabulary
  model/train.py       → model khud seekhta hai (backprop, no API)
  model/generate.py    → trained model chat/thinking karta hai
  model/model_card.json → model ki identity (naam, janam-tarikh, specs)
  data/corpus.txt       → model ki pehli "zindagi ki kitab" (seed knowledge)
  checkpoints/*.npz     → model ke weights save hote hain
