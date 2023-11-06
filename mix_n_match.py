import spacy

COMPOUNDS = ["compound"]
OBJECTS = ["dobj", "dative", "attr", "oprd", "pobj"]
# The user is green
def findSVCs(tokens):
    svcs = []
    verbs = [tok for tok in tokens if tok.pos_ == "AUX" and tok.dep_ == "ROOT"]
    print(verbs)
    for v in verbs:
        verb_passive=[]
        lefts = list(v.lefts)
        subs = [tok for tok in lefts if tok.dep_ in ["nsubj","nsubjpass"]]
        if len(subs) > 0:
            for sub in subs:
                print("subj: ",sub)
                sub_compound = generate_sub_compound(sub)
                rights=list(v.rights)
                comps=[tok for tok in rights if tok.dep_ == "acomp"]
                if len(comps)>0:
                    for comp in comps:
                        print("comps: ",comps)
                        svcs.append((" ".join(tok.lower_ for tok in sub_compound),
                                  v.lower_, (" ".join(tok.lower_ for tok in comps))))
                # I am in the homepage
                if v.nbor().dep_ == "prep":
                    next_to_verb = v.nbor()
                    print(type(next_to_verb))
                    n_subtree = next_to_verb.subtree
                    print([t.text for t in n_subtree])
                    span = tokens[next_to_verb.left_edge.i:next_to_verb.right_edge.i+1]
                    svcs.append((" ".join(tok.lower_ for tok in sub_compound),
                                 v.lower_, " ".join(t.text for t in span)))

    return svcs

def findSVOs(tokens):
    svos = []
    verbs = [tok for tok in tokens if tok.pos_ == "VERB" and tok.dep_ != "aux"]
    print(verbs)
    for v in verbs:
        verb_passive = []
        lefts = list(v.lefts)
        #print(v, [tok for tok in lefts])
        subs = [tok for tok in lefts if tok.dep_ in ["nsubj", "nsubjpass"]]
        #print(v,subs)
        if len(subs) > 0:
            for sub in subs:
                print("subj: ", sub)
                #sub_compound = generate_sub_compound(sub)
                rights = list(v.rights)
                print(v, sub, [tok for tok in rights])
                objs = [tok for tok in rights if tok.dep_ in OBJECTS]
                if len(objs) > 0:
                    for obj in objs:
                        print("objs: ", obj)
                        svos.append((sub, v.lower_, (" ".join(tok.lower_ for tok in objs))))
                else:
                    svos.append((sub.lower_,v.lower_, None))

    return svos


def generate_sub_compound(sub):
    sub_compunds = []
    for tok in sub.lefts:
        if tok.dep_ in COMPOUNDS:
            sub_compunds.extend(generate_sub_compound(tok))
    sub_compunds.append(sub)
    for tok in sub.rights:
        if tok.dep_ in COMPOUNDS:
            sub_compunds.extend(generate_sub_compound(tok))
    return sub_compunds

nlp = spacy.load("en_core_web_md", disable=["ner","textcat"])

sentence = u"""I am logged in as a user"""

doc = nlp(sentence)
for chunk in doc.noun_chunks:
    print(chunk.text)
for tok in doc:
    print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....",[left.text for left in tok.lefts], "....",[right.text for right in tok.rights])

print("SVCs: ",findSVCs(doc))
print("SVOs: ",findSVOs(doc))