import spacy
from spacy.matcher import Matcher

nlp=spacy.load("en_core_web_md")

#the user is logged in
#the user is signed in
#I am logged in
def user_matcher(doc):
    pattern = [{'DEP': 'nsubjpass', 'OP': '?'},
               {'LEMMA': 'be'},
               {'LEMMA': {"IN":['log','sign','register']}, 'POS': 'VERB'},
               {'ORTH': {"IN":['in','up','out']}}]
    matcher = Matcher(nlp.vocab)
    matcher.add("user", [pattern])
    matches = matcher(doc)
    if matches:
        for match_id, start, end in matches:
            return doc[start:end]

doc=nlp("I am logged in")

print(user_matcher(doc))

print(spacy.explain("acomp"))

ADJECTIVES = ["acomp", "advcl", "advmod", "amod", "appos", "nn", "nmod", "ccomp", "complm",
              "hmod", "infmod", "xcomp", "rcmod", "poss"," possessive"]

def getAdjectives(toks):
    toks_with_adjectives = []
    for tok in toks:
        adjs = [left for left in tok.lefts if left.dep_ in ADJECTIVES]
        print(adjs)
        adjs.append(tok)
        print(adjs)
        adjs.extend([right for right in tok.rights if tok.dep_ in ADJECTIVES])
        tok_with_adj = " ".join([adj.lower_ for adj in adjs])
        print(tok_with_adj)
        toks_with_adjectives.extend(adjs)
    return toks_with_adjectives


print(getAdjectives(nlp("I have a phone book")))
