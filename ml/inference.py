import torch
from init_classifier import tokenizer, model


THRESHOLD = 0.5


def toxicity_check(text: str,
                  aggregate: bool = True) -> bool:
    '''
        returns True if message contains toxic words,
        otherwise returns False
        message should be converted in string
    '''

    # """ Calculate toxicity of a text (if aggregate=True) or a vector of toxicity aspects (if aggregate=False)"""
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True).to(model.device)
        proba = torch.sigmoid(model(**inputs).logits).cpu().numpy()
    if isinstance(text, str):
        proba = proba[0]
    # if aggregate:
    #     return 1 - proba.T[0] * (1 - proba.T[-1])
    # return proba
    
    score = 1 - proba.T[0] * (1 - proba.T[-1])
    if score >= THRESHOLD:
        return True
    return False
