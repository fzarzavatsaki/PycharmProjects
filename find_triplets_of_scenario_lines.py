import spacy
from spacy.lang.en import English
from spacy.tokens import Token
from spacy import displacy
from pathlib import Path
from spacy.lang.en import English
from spacy.matcher import Matcher
from spacy.tokens import Span
from spacy.language import Language
import textacy
from textacy import extract
from svao import findSVOs
from svao import findSVCs
from svao import findSVAOs
from pre_conditions_running_docs import features
from pre_conditions import pre_conditions, actions, post_conditions



SUBJECTS = ["nsubj", "nsubjpass", "pobj"]
OBJECTS = ["pobj", "dobj", "attr", "conj", "acomp"]
COMPOUNDS = ["compound", "amod"]

def generate_obj_compound(obj):
    obj_compunds = []
    for tok in obj.lefts:
        if tok.dep_ in COMPOUNDS:
            obj_compunds.extend(generate_obj_compound(tok))
    obj_compunds.append(obj)
    #print(obj_compunds)
    for tok in obj.rights:
        if tok.dep_ in COMPOUNDS:
            obj_compunds.extend(generate_obj_compound(tok))
        #print(obj_compunds)
    return obj_compunds

#doc1= nlp(""" The password needs to contain at least one number and one capital letter""")

#objs = [tok for tok in doc1 if tok.dep_ in ["dobj","conj"]]
#compound_objects=[]
#for obj in objs:
    #obj_compound= generate_obj_compound(obj)
    #compound_objects.append(" ".join(tok.lower_ for tok in obj_compound))
    #print(compound_objects)

def generate_subj_compound(subj):
    subj_compounds = []
    for tok in subj.lefts:
        if tok.dep_ in COMPOUNDS:
            subj_compounds.extend(generate_subj_compound(tok))
    subj_compounds.append(subj)
    for tok in subj.rights:
        if tok.dep_ in COMPOUNDS:
            subj_compounds.extend(generate_obj_compound(tok))

    return subj_compounds

# Extract objs with conjunction eg I should be able to share the selected route and rating
def getObjsFromConjunctions(objs):
    moreObjs = []
    for obj in objs:
        # rights is a generator
        rights = list(obj.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if "and" or "," in rightDeps:
            moreObjs.extend([tok for tok in rights if tok.dep_ in OBJECTS or tok.pos_ == "NOUN"])
            if len(moreObjs) > 0:
                moreObjs.extend(getObjsFromConjunctions(moreObjs))
    return moreObjs

def attr_extraction(tok):
    rights = [t for t in tok.rights]
    attr = []
    for tok in rights:
        if tok.dep_ == "prep" and tok.pos_ == "ADP":
            tok_rights = [t for t in tok.rights]
            for t in tok_rights:
                if t.dep_ == "pobj" and t.pos_ == "NOUN":
                    attr.append(t)
    return attr

def get_verbs_from_sec(verb):
    print("tok", type(verb))
    tok_rights = tok.rights
    objs = []
    new_verbs = []
    for t in tok_rights:
        if t.pos_ == "NOUN" and t.dep_ == "dobj":
            objs.append(t)
        if len(objs) > 0:
            for obj in objs:
                right = obj.rights
                new_verbs.append(t for t in tok_rights if t.pos_ == "VERB")
    return new_verbs


def stepVerbs(doc):
    svos = []
    verbs = [tok for tok in doc if tok.pos_ in ["VERB", "AUX"]]
    for v in verbs:
        print("v",v)
        other_verbs=get_verbs_from_sec(v)
        print("other_verbs", other_verbs)
        verbs.extend(other_verbs)
    for v in verbs:
        if "log" in v.text and v.dep_ == "ROOT":       # I am logged in as a user
            subs = [tok for tok in v.lefts if tok.dep_ in SUBJECTS and tok.pos_ != "DET"]
            for sub in subs:
                subj_compounds = generate_subj_compound(sub)
            if len(subs) > 0:
                rights = [tok for tok in v.rights]
                print("rights", rights, [r.dep_ for r in rights])
                for tok in rights:
                    if tok.pos_ == "ADP" and tok.dep_ == "prep":
                        print([t for t in tok.rights])
                        objs = [t for t in tok.rights if t.dep_ == "pobj"]
                        print(tok, "objs",objs)
                        if len(objs) > 0:
                            objs.extend(getObjsFromConjunctions(objs))
                            for obj in objs:
                                objs_compounds = generate_obj_compound(obj)
                                svos.append((" ".join(tok.lower_ for tok in subj_compounds),v.lower_, " ".join(tok.lower_ for tok in objs_compounds)))
                    else:
                         svos.append((" ".join(tok.lower_ for tok in subs), v.lower_, None))       # I am logged in
        else:
            if v.dep_ != "aux" and v.tag_ != "VBN":  # Subject verb object active voice
                print("verb: ", v, v.tag_, spacy.explain(v.tag_))
                objs = []
                subs = [tok for tok in v.lefts if tok.dep_ in SUBJECTS and tok.pos_ != "DET"]
                if len(subs) >0:
                    for sub in subs:
                        sub_compounds = generate_subj_compound(sub)
                        print("sub_comp", sub_compounds)
                    rights = [tok for tok in v.rights]
                    if rights:
                        for tok in rights:
                            if tok.text == "option":  # I should have the option to cancel the order
                                option_objs = []      # Find the object of the second verb
                                rights = list(tok.rights)
                                print("rights", rights)
                                for t in rights:
                                    if t.pos_ == "VERB":
                                        option_verb = t
                                        print("option verb", option_verb)
                                        for t in option_verb.rights:
                                            if t.dep_ == "dobj":
                                                option_objs.append(t)
                                            option_objs.extend(getObjsFromConjunctions(option_objs))  # In order to create triplets with all the conjunct objects
                                        obj_attrs = []
                                        if option_objs:
                                            for obj in option_objs:
                                                obj_attrs.extend(attr_extraction(obj))
                                                objs_compounds = generate_obj_compound(obj)
                                                svos.append((" ".join(tok.lower_ for tok in sub_compounds), option_verb.lower_, " ".join(tok.lower_ for tok in objs_compounds),
                                                         " ".join(tok.lower_ for tok in obj_attrs)))
                                        else:
                                            svos.append((" ".join(tok.lower_ for tok in subs), option_verb.lower_, None))
                            elif tok.dep_ in OBJECTS and tok.text != "able":
                                objs.append(tok)
                                print("objs", objs)
                            elif tok.dep_ == "xcomp" and tok.pos_ == "VERB":  #The user wants to delete an event
                                v = tok
                                for t in tok.rights:
                                    if t.dep_ == "dobj" and t.pos_ == "NOUN":
                                        objs.append(t)
                            elif tok.text == "able":    # I should be able to cancel the order
                                rights = tok.rights
                                for t in rights:
                                    if t.dep_ == "xcomp" and t.pos_ == "VERB":
                                        v = t
                                        for t in v.rights:
                                            if t.dep_ == "dobj":
                                                objs.append(t)
                        if len(objs) >0:
                            objs.extend(getObjsFromConjunctions(objs)) # In order to create triplets with all the conjunct objects
                            obj_attrs = []
                            for obj in objs:
                                obj_attrs.extend(attr_extraction(obj))
                                objs_compounds = generate_obj_compound(obj)
                                svos.append((" ".join(tok.lower_ for tok in sub_compounds),v.lower_, " ".join(tok.lower_ for tok in objs_compounds), " ".join(tok.lower_ for tok in obj_attrs)))
                        else:
                            svos.append((" ".join(tok.lower_ for tok in subs), v.lower_, None))
                    else:
                        svos.append((" ".join(tok.lower_ for tok in subs), v.lower_, None))
            elif v.dep_ != "aux" and v.tag_ == "VBN":   # subject verb object past participle
                print("verb: ", v, v.tag_, spacy.explain(v.tag_))
                objs = []
                asubs = []
                lefts = [tok for tok in v.lefts]
                for tok in lefts:
                    if tok.dep_ == "nsubj":
                        asubs.append(tok)
                        if len(asubs) > 0:
                            rights = [tok for tok in v.rights]
                            if rights:
                                for tok in rights:
                                    if tok.dep_ in OBJECTS:
                                        objs.append(tok)
                                    elif tok.dep_ == "xcomp" and tok.pos_ == "VERB":  # The user wants to delete an event
                                        v = tok
                                        for t in tok.rights:
                                            if t.dep_ == "dobj":
                                                objs.append(t)
                                    if len(objs) > 0:
                                        objs.extend(getObjsFromConjunctions(objs))
                                        for obj in objs:
                                            objs_compounds = generate_obj_compound(obj)
                                            svos.append((" ".join(tok.lower_ for tok in asubs), v.lower_,obj.lower_))
                                    else:
                                        svos.append((" ".join(tok.lower_ for tok in asubs), v.lower_, None))
                            else:
                                svos.append((" ".join(tok.lower_ for tok in asubs), v.lower_, None))
                    elif tok.dep_ == "nsubjpass":  # svo passive voice
                        print("subj_tok", tok)
                        subs = []
                        objs = [tok for tok in v.lefts if tok.dep_ == "nsubjpass" and tok.pos_ != "DET"]
                        print("pass_obj", objs)
                        rights = [t for t in v.rights]
                        if rights:
                            for t in rights:                 # I should be asked to insert the route parameters
                                if t.pos_ == "VERB":         # Find the second triplet (I, insert, parameters)
                                    second_verb_objs = []
                                    second_verb_subs = []
                                    second_verb = t
                                    print("tok",tok)
                                    second_verb_subs.extend(objs)
                                    for t in second_verb.rights:
                                        if t.dep_ == "dobj":
                                            second_verb_objs.append(t)
                                    svos.append((" ".join(tok.lower_ for tok in second_verb_subs), second_verb.lower_, " ".join(tok.lower_ for tok in second_verb_objs)))
                                else:
                                    print("objs",objs)
                                    if len(objs) >0:
                                        rights = [tok for tok in v.rights]
                                        for tok in rights:
                                            if tok.dep_ in OBJECTS:
                                                subs.append(tok)
                                            elif tok.pos_ == "ADP" and tok.dep_ == "agent":
                                                for t in tok.rights:
                                                    if t.dep_ == "pobj":
                                                        subs.append(t)
                                if len(subs) >0:
                                    svos.append((" ".join(tok.lower_ for tok in subs),v.lower_, " ".join(tok.lower_ for tok in objs)))
                                else:
                                    svos.append((None, v.lower_, " ".join(tok.lower_ for tok in objs)))
                        else:
                            svos.append((None, v.lower_, " ".join(tok.lower_ for tok in objs)))

            LINKING_VERBS = ["ccomp", "ROOT"]
            #if v.pos_ == "AUX" and v.dep_ in LINKING_VERBS:
                #subs = [t for t in v.lefts if t.pos_ == "NOUN"]
                #obj_attrs =[]
                #objs = [t for t in v.rights if t.dep_ == "acomp"]
                #print("is_objs", objs)
                #if len(objs) > 0:
                    #for sub in subs:
                        #sub_compounds = generate_subj_compound(sub)
                        #print("sub_comp", sub_compounds)
                        #for obj in objs:
                            #obj_attrs.extend(attr_extraction(obj))
                            #objs_compounds = generate_obj_compound(obj)
                            #print("obj_comp", objs_compounds)
                            #svos.append((" ".join(tok.lower_ for tok in sub_compounds), v.lower_,
                                         #" ".join(tok.lower_ for tok in objs_compounds),
                                         #" ".join(tok.lower_ for tok in obj_attrs)))
                #else:
                    #svos.append((" ".join(tok.lower_ for tok in subs), v.lower_, None))


    return svos
#print ("Pre_conditions ", pre_conditions)
#for condition in pre_conditions:
    #print(stepVerbs(condition))

for feature in features:
    for scenario in feature["Scenarios"]:
        print(scenario)
        for step in scenario["When"]:
            for tok in step:
                print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....",
                      [left.text for left in tok.lefts], "....",[right.text for right in tok.rights])
            print("When triplets: ",stepVerbs(step))

        for step in scenario["Given"]:
            for tok in step:
                print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....", [left.text for left in tok.lefts], "....",[right.text for right in tok.rights])
            print("Given triplets: ",stepVerbs(step))

        for step in scenario["Then"]:
            for tok in step:
                print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....", [left.text for left in tok.lefts], "....",[right.text for right in tok.rights])
            print("Then triplets: ", stepVerbs(step))
#print(spacy.explain("pcomp"))