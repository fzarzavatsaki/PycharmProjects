
import spacy


SUBJECTS = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
OBJECTS = ["dobj", "dative", "attr", "oprd","npadvmod","conj"]
ADJECTIVES = ["acomp", "advcl", "advmod", "amod", "appos", "nn", "nmod", "nummod","ccomp", "complm",
              "hmod", "infmod", "xcomp", "rcmod", "poss","possessive"]
COMPOUNDS = ["compound"]
PREPOSITIONS = ["prep"]

def getSubsFromConjunctions(subs):
    moreSubs = []
    for sub in subs:
        # rights is a generator
        rights = list(sub.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if "and" in rightDeps:
            moreSubs.extend([tok for tok in rights if tok.dep_ in SUBJECTS or tok.pos_ == "NOUN"])
            if len(moreSubs) > 0:
                moreSubs.extend(getSubsFromConjunctions(moreSubs))
    return moreSubs

def getObjsFromConjunctions(objs):
    moreObjs = []
    for obj in objs:
        # rights is a generator
        rights = list(obj.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if "and" in rightDeps:
            moreObjs.extend([tok for tok in rights if tok.dep_ in OBJECTS or tok.pos_ == "NOUN"])
            if len(moreObjs) > 0:
                moreObjs.extend(getObjsFromConjunctions(moreObjs))
    return moreObjs

def getVerbsFromConjunctions(verbs):
    moreVerbs = []
    for verb in verbs:
        rightDeps = {tok.lower_ for tok in verb.rights}
        if "and" in rightDeps:
            moreVerbs.extend([tok for tok in verb.rights if tok.pos_ == "VERB"])
            if len(moreVerbs) > 0:
                moreVerbs.extend(getVerbsFromConjunctions(moreVerbs))
    return moreVerbs


def getAllSubs(v):
    verbNegated = isNegated(v)
    subs = [tok for tok in v.lefts if tok.dep_ in SUBJECTS and tok.pos_ != "DET"]
    print("verb: ",v,"subjects: ",subs)
    if len(subs) > 0:
        subs.extend(getSubsFromConjunctions(subs))
    else:
        foundSubs, verbNegated = findSubs(v)
        subs.extend(foundSubs)
    return subs ,verbNegated

def findSVs(tokens):
    svs = []
    verbs = [tok for tok in tokens if tok.pos_ == "VERB"]
    for v in verbs:
        subs, verbNegated = getAllSubs(v)
        if len(subs) > 0:
            for sub in subs:
                svs.append((sub.orth_, "!" + v.orth_ if verbNegated else v.orth_))
    return svs

def getObjsFromPrepositions(deps):
    objs = []
    for dep in deps:
        if dep.pos_ == "ADP" and dep.dep_ == "prep":
            objs.extend([tok for tok in dep.rights if tok.dep_  in OBJECTS or (tok.pos_ == "PRON" and tok.lower_ == "me")])
    return objs

def getAdjectives(toks):
    toks_with_adjectives = []
    for tok in toks:
        adjs = [left for left in tok.lefts if left.dep_ in ADJECTIVES]
        adjs.append(tok)
        adjs.extend([right for right in tok.rights if tok.dep_ in ADJECTIVES])
        tok_with_adj = " ".join([adj.lower_ for adj in adjs])
        toks_with_adjectives.extend(adjs)

    return toks_with_adjectives

def getObjsFromAttrs(deps):
    for dep in deps:
        if dep.pos_ == "NOUN" and dep.dep_ == "attr":
            verbs = [tok for tok in dep.rights if tok.pos_ == "VERB"]
            if len(verbs) > 0:
                for v in verbs:
                    rights = list(v.rights)
                    objs = [tok for tok in rights if tok.dep_ in OBJECTS]
                    objs.extend(getObjsFromPrepositions(rights))
                    if len(objs) > 0:
                        return v, objs
    return None, None

def getObjFromXComp(deps):
    for dep in deps:
        if dep.pos_ == "VERB" and dep.dep_ == "xcomp":
            v = dep
            rights = list(v.rights)
            objs = [tok for tok in rights if tok.dep_ in OBJECTS]
            objs.extend(getObjsFromPrepositions(rights))
            if len(objs) > 0:
                return v, objs
    return None, None
def getAllObjsWithAdjectives(v):
    # rights is a generator
    rights = list(v.rights)
    objs = [tok for tok in rights if tok.dep_ in OBJECTS]
    print("objs???",objs)

    if len(objs)== 0:
        objs = [tok for tok in rights if tok.dep_ in ADJECTIVES]

    objs.extend(getObjsFromPrepositions(rights))

    potentialNewVerb, potentialNewObjs = getObjFromXComp(rights)
    if potentialNewVerb is not None and potentialNewObjs is not None and len(potentialNewObjs) > 0:
        objs.extend(potentialNewObjs)
        v = potentialNewVerb
    if len(objs) > 0:
        objs.extend(getObjsFromConjunctions(objs))
    print("verb: ",v,"objects: ",objs)
    return v, objs

def getAllObjs(v):
    # rights is a generator
    rights = list(v.rights)
    print("verb:","rights: ",rights)
    objs = [tok for tok in rights if tok.dep_ in OBJECTS]
    print("Objects: ",objs)
    objs.extend(getObjsFromPrepositions(rights))

    potentialNewVerb, potentialNewObjs = getObjFromXComp(rights)
    if potentialNewVerb is not None and potentialNewObjs is not None and len(potentialNewObjs) > 0:
        objs.extend(potentialNewObjs)
        v = potentialNewVerb
    if len(objs) > 0:
        objs.extend(getObjsFromConjunctions(objs))
        return v, objs
    else:
        return v,[]

def findSubs(tok):
    head = tok.head
    while head.pos_ != "VERB" and head.pos_ != "NOUN" and head.head != head:
        head = head.head
    if head.pos_ == "VERB":
        subs = [tok for tok in head.lefts if tok.dep_ in SUBJECTS]
        if len(subs) > 0:
            verbNegated = isNegated(head)
            subs.extend(getSubsFromConjunctions(subs))
            return subs, verbNegated
        elif head.head != head:
            return findSubs(head)
    elif head.pos_ == "NOUN":
        return [head], isNegated(tok)
    return [], False

def isNegated(tok):
    negations = {"no", "not", "n't", "never", "none"}
    for dep in list(tok.lefts) + list(tok.rights):
        if dep.lower_ in negations:
            return True
    return False

def findSVOs(tokens):
    svos = []
    verbs = [tok for tok in tokens if tok.pos_ == "VERB" and tok.dep_ !="AUX"]
    print("verbs: ",verbs)
    for v in verbs:
        subs, verbNegated = getAllSubs(v)
        print("verb: ", v, "subjects: ", subs)
        # hopefully there are subs, if not, don't examine this verb any longer
        if len(subs) > 0:
            v, objs = getAllObjs(v)
            print("verb: ",v,"objects: ",objs)
            for sub in subs:
                sub_compound = generate_sub_compound(sub)
                if len(objs) > 0:
                    for obj in objs:
                        objNegated = isNegated(obj)
                        # obj_desc_tokens = generate_left_right_adjectives(obj)
                        # for obj in obj_desc_tokens:
                        objs_compound = generate_obj_compound(obj)
                        svos.append((" ".join(tok.lower_ for tok in sub_compound),
                                     "!" + v.lower_ if verbNegated or objNegated else v.lower_,
                                     " ".join(tok.lower_ for tok in objs_compound)))
                else:
                    svos.append(
                        (" ".join(tok.lower_ for tok in sub_compound), "!" + v.lower_ if verbNegated else v.lower_))
            return svos

def findSVAOs(tokens):
    svaos = []
    verbs = [tok for tok in tokens if tok.pos_ == "VERB" and tok.dep_ !="AUX"]
    print("verbs: ",verbs)
    for v in verbs:
        subs, verbNegated = getAllSubs(v)
        print("verb: ", v, "sub: ",subs)
        # hopefully there are subs, if not, don't examine this verb any longer
        if len(subs) > 0:
            v, objs = getAllObjsWithAdjectives(v)
            print("v", v, "obj...",objs)
            for sub in subs:
                if len(objs)>0:
                    for obj in objs:
                        objNegated = isNegated(obj)
                        #obj_desc_tokens = generate_left_right_adjectives(obj)
                        #for obj in obj_desc_tokens:
                        sub_compound = generate_sub_compound(sub)
                        objs_compound= generate_obj_compound(obj)
                        print("compounds: ",objs_compound)
                        svaos.append((" ".join(tok.lower_ for tok in sub_compound), "!" + v.lower_ if verbNegated or objNegated else v.lower_, " ".join(tok.lower_ for tok in objs_compound)))
                else:
                    []
                    #svaos.append((" ".join(tok.lower_ for tok in sub_compound), "!" + v.lower_ if verbNegated else v.lower_))
    return svaos

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

def generate_obj_compound(obj):
    obj_compunds = []
    for tok in obj.lefts:
        if tok.dep_ in COMPOUNDS:
            obj_compunds.extend(generate_obj_compound(tok))
    obj_compunds.append(obj)
    for tok in obj.rights:
        if tok.dep_ in COMPOUNDS:
            obj_compunds.extend(generate_obj_compound(tok))
    return obj_compunds

def generate_left_right_adjectives(obj):
    obj_desc_tokens = []
    for tok in obj.lefts:
        if tok.dep_ in ADJECTIVES:
            obj_desc_tokens.extend(generate_left_right_adjectives(tok))
    obj_desc_tokens.append(obj)

    for tok in obj.rights:
        if tok.dep_ in ADJECTIVES:
            obj_desc_tokens.extend(generate_left_right_adjectives(tok))

    return obj_desc_tokens

# New trying to parse the username is valid
def findSVCs(tokens):
    svcs = []
    verbs = [tok for tok in tokens if tok.pos_ == "AUX" and tok.dep_ == "ROOT"]
    print(verbs)
    for v in verbs:
        verb_passive=[]
        lefts=list(v.lefts)
        subs=[tok for tok in lefts if tok.dep_ in ["nsubj","nsubjpass"]]
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
    return svcs


nlp = spacy.load("en_core_web_md", disable=["ner","textcat"])
from pre_conditions import post_conditions

#for doc in post_conditions:
sentence = u"""Given I am logged in as a user"""

doc = nlp(sentence)
frag = doc[1:]
for chunk in frag.noun_chunks:
    print(chunk.text)
for tok in frag:
    print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....",[left.text for left in tok.lefts], "....",[right.text for right in tok.rights])
print("svaos",findSVAOs(frag))
print("svos",findSVOs(frag))
print("svcs", findSVCs(frag))
