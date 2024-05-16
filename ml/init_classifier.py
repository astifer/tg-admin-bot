from transformers import BertTokenizer, BertForSequenceClassification


tokenizer: BertTokenizer = BertTokenizer.from_pretrained('SkolkovoInstitute/russian_toxicity_classifier')
model: BertForSequenceClassification = BertForSequenceClassification.from_pretrained('SkolkovoInstitute/russian_toxicity_classifier')
model.eval()

print("Downloaded Toxicity Classifiers Succesfully!")