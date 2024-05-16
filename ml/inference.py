import torch
from init_classifier import tokenizer, model


THRESHOLD = 0.5


def toxicity_check(message: str) -> bool:
    '''
        returns True if message contains toxic words,
        otherwise returns False
        message should be converted in string
    '''
    batch = tokenizer.encode(message, return_tensors='pt')
    probs = torch.softmax(model(batch).logits, dim=-1).squeeze(0)

    if probs[1].item() >= THRESHOLD:
        return True
    
    return False
