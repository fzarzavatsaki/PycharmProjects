import spacy

nlp = spacy.load("en_core_web_md")

ADJECTIVES = ["acomp", "advcl", "advmod", "amod", "appos", "nn", "nmod", "ccomp", "complm",
              "hmod", "infmod", "xcomp", "rcmod", "poss"," possessive"]
SUBJECTS = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
OBJECTS=["dobj", "dative", "attr", "oprd", "pobj"]


def find_SVOS(doc):
    svos=[]
    verbs= [tok for tok in doc if tok.pos_ in ["VERB","AUX"]]
    for v in verbs:
        if v.dep_=="ROOT" and v.pos_ != "AUX":
            subs= getAllSubs(v)
            if len(subs)>0:
                v,objs = getAllObjects(v)
                for sub in subs:
                    for obj in objs:
                        svos.append((sub.lower_, v.lower_,obj.lower_))
        elif v.dep_=="ROOT" and v.pos_ == "AUX":
            v_rights=list(v.rights)
            v_rights_pos=[tok.pos_ for tok in v_rights]
            if "ADJ" in v_rights_pos:

                verbs.extend(" ".join)
    return svos

def getAllSubs(doc):
    verbs = [tok for tok in doc if tok.pos_ in ["VERB", "AUX"]]
    print(verbs)
    for v in verbs:
        v_lefts = list(v.lefts)
        print(v.lefts)
        subs = [tok for tok in v.lefts if tok.dep_ in SUBJECTS and tok.pos_ != "DET"]
        if len(subs) > 0:
            return subs
        else:
            return None

def getAllObjects(v):
    rights=list(v.rights)
    objs = [tok for tok in v.rights if tok.dep_ in OBJECTS]
    if len(objs)>0:
        print(objs)
        return v, objs
    else:
        return None



sentence = u""" the user is registerd and logged in """

doc = nlp(sentence)
for chunk in doc.noun_chunks:
    print(chunk.text)
for tok in doc:
    print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....",tok.left_edge.text,"....", tok.right_edge.text,"....",[left.text for left in tok.lefts], "....",[right.text for right in tok.rights])

print(getAllSubs(doc))
