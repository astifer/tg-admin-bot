import pytest
from ml.inference import toxicity_check
from ml.inference import THRESHOLD

print(f"Threshold: {THRESHOLD}\n")


@pytest.mark.ml_test
def test_discrimination():
    text_toxic_label = {
        "you are nigger": True,
        "ты красава": False,
        "Давить вас надо, сепоров сраных": True
    }

    for text, label in text_toxic_label:
        assert toxicity_check(text) == label


@pytest.mark.ml_test
def test_badwords():
    text_toxic_label = {
        "пошел ты нах": True,
        "закапывать семена растений глубоко не нужно": False,
        "епта, такого я не ожидал": True,
        "неудивил бля": True
    }

    for text, label in text_toxic_label:
        assert toxicity_check(text) == label
