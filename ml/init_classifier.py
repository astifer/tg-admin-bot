# !pip install transformers sentencepiece --quiet
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


model_checkpoint = 'cointegrated/rubert-tiny-toxicity'
tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
model: AutoModelForSequenceClassification = AutoModelForSequenceClassification.from_pretrained(
    model_checkpoint
)
if torch.cuda.is_available():
    model.cuda()


# print(text2toxicity('я люблю нигеров', True))
print("Downloaded successfully.")
