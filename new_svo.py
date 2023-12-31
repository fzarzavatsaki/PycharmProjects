import spacy
nlp = spacy.load("en_core_web_sm")

# object and subject constants
OBJECT_DEPS = {"dobj", "dative", "attr", "oprd", "nsubjpass"}
SUBJECT_DEPS = {"nsubj", "csubj", "agent", "expl"}
# tags that define whether the word is wh-
WH_WORDS = {"WP", "WP$", "WRB"}

# extract the subject, object and verb from the input
def extract_svo(doc):
    sub = []
    at = []
    ve = []
    for token in doc:
        # is this a verb?
        if token.pos_ == "VERB":
            rights = list(token.rights)
            #rightDeps = {tok.lower_ for tok in rights}
            for tok in rights:
                 if tok.dep_ in ['prep', 'prt']:
                    verb_w_prn = token.text + " " + tok.text
                    ve.append(verb_w_prn)
                    continue
            ve.append(token.text)
        # is this the object?
        if token.dep_ in OBJECT_DEPS or token.head.dep_ in OBJECT_DEPS:
            at.append(token.text)
        # is this the subject?
        if token.dep_ in SUBJECT_DEPS or token.head.dep_ in SUBJECT_DEPS:
            sub.append(token.text)
    return " ".join(sub).strip().lower(), " ".join(ve).strip().lower(), " ".join(at).strip().lower()

# wether the doc is a question, as well as the wh-word if any
def is_question(doc):
    # is the first token a verb?
    if len(doc) > 0 and doc[0].pos_ == "VERB":
        return True, ""
    # go over all words
    for token in doc:
        # is it a wh- word?
        if token.tag_ in WH_WORDS:
            return True, token.text.lower()
    return False, ""

# gather the user input and gather the info
while True:
    doc = nlp(input("> "))
    # print out the pos and deps
    for token in doc:
        print("Token {} POS: {}, dep: {}, head:{}".format(token.text, token.pos_, token.dep_, token.head, [left.text for left in token.lefts], "....",[right.text for right in token.rights]))

    # get the input information
    subject, verb, attribute = extract_svo(doc)
    question, wh_word = is_question(doc)
    print("svo:, subject: {}, verb: {}, attribute: {}, question: {}, wh_word: {}".format(subject, verb, attribute, question, wh_word))