import spacy
from preprocessing import preprocessing


nlp = spacy.load("en_core_web_lg")

# _______________________________________________ #
# These are the subject, object, compound dependencies used in this algorithm

subjects = ["nsubj", "nsubjpass", "pobj"]
objects = ["pobj", "dobj", "attr", "conj", "acomp"]
compounds = ["compound", "amod"]

doc = nlp("I am informed the offer is successfully updated")
#displacy.serve(doc, style="dep")


# ___________________________________________________ #
# Find the compound nouns of the steps

def find_compounds(tok):
    tok_compounds = []
    # Iterate through the token's lefts
    for left in tok.lefts:
        if left.dep_ in compounds:
            # Recursively process additional compounds of the token
            tok_compounds.extend(find_compounds(left))
    tok_compounds.append(tok)
    # Iterate through the token's rights
    for right in tok.rights:
        if right.dep_ in compounds:
            # Recursively process additional compounds of the token
            tok_compounds.extend(find_compounds(right))
    return tok_compounds


# __________________________________________ #
# Extract objects from conjunctions
# eg I should be able to share the selected route and rating

def find_objects_from_conjunc(objs):
    new_objects = []
    for obj in objs:
        # Iterate through the object's children
        for child in obj.rights:
            if child.lower_ in ["and", "or", ","]:  # Check for conjunctions
                # Explore the siblings of the conjunction token to find associated objects
                for sibling in child.head.children:
                    if sibling.dep_ in objects or sibling.pos_ == "NOUN":
                        new_objects.append(sibling)
    # Recursively process additional objects found through conjunctions
    if new_objects:
        new_objects.extend(find_objects_from_conjunc(new_objects))
    return new_objects


# _______________________________________ #
# Get objects introduced with prepositions

def find_objects_from_preps(token):
    new_objects = []
    for child in token.children:
        if child.dep_ == "prep":
            for obj in child.children:
                if obj.dep_ in objects:
                    new_objects.append(obj)
    return new_objects


# ___________________________________________________________________ #
# The function that creates the Subject Verb Object triplets of a step

def step_svo(doc):
    svos = []
    verbs = [tok for tok in doc if tok.pos_ in ["VERB", "AUX"]]

    for verb in verbs:
        if "log" in verb.text or "sign" in verb.text:   # I am logged in as a user
            #print("log verb", verb)
            subs = [tok for tok in verb.lefts if tok.dep_ in subjects and tok.pos_ != "DET"]

            # Add the in, out, up adverb after the verb
            next_token = doc[verb.i] if verb.i < len(doc) else None  # doc[verb.i] is the next token after the verb
            if next_token and next_token.pos_ in ["ADV", "ADP"]:
                new_verb = verb.lemma_.lower() + " " + next_token.text.lower()
            else:
                new_verb = verb.lemma_.lower()

            if subs:
                for sub in subs:
                    subj_compounds = find_compounds(sub)
                    # First triplet: Subject ("I"), Verb ("log"), None (no object)
                    svos.append((" ".join(tok.lower_ for tok in subj_compounds), new_verb, None))

            for tok in verb.rights:
                if tok.pos_ == "ADP" and tok.dep_ == "prep" and tok.text.lower() == "as":
                    role = None
                    for t in tok.rights:
                        if t.dep_ == "pobj":
                            role = t.text.lower()
                            #print("role", role)
                            break
                    if role is not None:
                        # Second triplet: Subject ("Role"), Verb ("log"), None (no object)
                        svos.append((role, new_verb, None))

        else:
            # Subject Verb Object Active Voice
            if verb.pos_ != "AUX" and verb.tag_ != "VBN":
                #print("verb active:", verb, verb.dep_, verb.pos_)
                objs = []
                subs = [tok for tok in verb.lefts if tok.dep_ in subjects and tok.pos_ != "DET"]
                if subs:
                    for sub in subs:
                        sub_compounds = find_compounds(sub)
                    rights = [tok for tok in verb.rights]
                    if rights:
                        for tok in rights:
                            if tok.text == "option":  # I should have the option to cancel the order
                                option_objs = []      # Find the object of the second verb
                                rights = list(tok.rights)
                                for t in rights:
                                    if t.pos_ == "VERB":
                                        option_verb = t
                                        #print("option verb", option_verb)
                                        for t in option_verb.rights:
                                            if t.dep_ == "dobj":
                                                option_objs.append(t)
                                            option_objs.extend(find_objects_from_preps(option_verb))  # I have the option to search for a restaurant (prep +pobj)
                                            option_objs.extend(find_objects_from_conjunc(option_objs))  # Extend the option_objs with objects from conjunctions
                                        if option_objs:
                                            for obj in option_objs:
                                                objs_compounds = find_compounds(obj)
                                                svos.append((" ".join(tok.lower_ for tok in sub_compounds), option_verb.lemma_,
                                                             " ".join(tok.lower_ for tok in objs_compounds)))
                                        else:
                                            svos.append((" ".join(tok.lower_ for tok in sub_compounds), option_verb.lemma_, None))
                            elif tok.dep_ in objects and tok.text != "able":
                                objs.append(tok)
                                #print("objs", objs)
                            elif tok.dep_ == "xcomp" and tok.pos_ == "VERB":  #The user wants to delete an event
                                verb = tok
                                for t in tok.rights:
                                    if t.dep_ == "dobj" and t.pos_ == "NOUN":
                                        objs.append(t)
                            elif tok.text == "able":    # I should be able to cancel the order
                                rights = list(tok.rights)
                                for t in rights:
                                    if t.dep_ == "xcomp" and t.pos_ == "VERB":
                                        verb = t
                                        for t in verb.rights:
                                            if t.dep_ == "dobj":
                                                objs.append(t)
                                            objs.extend(find_objects_from_preps(verb)) # I should be able to search for a restaurant
                        if objs:
                            objs.extend(find_objects_from_conjunc(objs))  # Create triplets with all the conjunct objects
                            for obj in objs:
                                objs_compounds = find_compounds(obj)
                                svos.append((" ".join(tok.lower_ for tok in sub_compounds),verb.lemma_, " ".join(tok.lower_ for tok in objs_compounds)))
                        else:
                            svos.append((" ".join(tok.lower_ for tok in sub_compounds), verb.lemma_, None))
                    else:
                        svos.append((" ".join(tok.lower_ for tok in sub_compounds), verb.lemma_, None))

            # # Subject Verb Object Past Participle # #

            elif verb.pos_ != "aux" and verb.tag_ == "VBN":
                #print("verb participle: ", verb, verb.tag_, spacy.explain(verb.tag_))
                objs = []
                asubs = []
                lefts = [tok for tok in verb.lefts]
                for tok in lefts:
                    #print("left", tok, tok.dep_)
                    if tok.dep_ == "nsubj":
                        asubs.append(tok)
                        #print("asubj", [t for t in asubs])
                        if asubs:
                            rights = [tok for tok in verb.rights]
                            if rights:
                                for tok in rights:
                                    if tok.dep_ in objects and tok not in objs and tok.pos_ != "VERB":
                                        objs.append(tok)
                                    elif tok.dep_ == "xcomp" and tok.pos_ == "VERB":  # The user wants to delete an event
                                        verb = tok
                                        for t in tok.rights:
                                            if t.dep_ == "dobj":
                                                objs.append(t)
                                            objs.extend(find_objects_from_preps(verb))
                                    if objs:
                                        objs.extend(find_objects_from_conjunc(objs))
                                        for obj in objs:
                                            objs_compounds = find_compounds(obj)
                                            svos.append((" ".join(tok.lower_ for tok in asubs), verb.lemma_," ".join(tok.lower_ for tok in objs_compounds)))
                                    else:
                                        svos.append((" ".join(tok.lower_ for tok in asubs), verb.lemma_, None))
                            else:
                                svos.append((" ".join(tok.lower_ for tok in asubs), verb.lemma_, None))

                    # _________________________________ #
                    # Subject Verb Object Passive Voice #

                    elif tok.dep_ == "nsubjpass":
                        subs = []
                        objs = [tok for tok in verb.lefts if tok.dep_ == "nsubjpass" and tok.pos_ != "DET"]
                        rights = [t for t in verb.rights]
                        #print("rights ", rights)
                        if rights:
                            for t in rights:                 # I should be asked to insert the route parameters
                                if t.pos_ == "VERB":         # Find the second triplet (I, insert, parameters)
                                    second_verb_objs = []
                                    second_verb_subs = []
                                    second_verb = t
                                    second_verb_subs.extend(objs)
                                    for token in second_verb.rights:
                                        if token.dep_ == "dobj":
                                            second_verb_objs.append(token)
                                        second_verb_objs.extend(find_objects_from_preps(second_verb))  # I should be asked to search for a new address
                                    if second_verb_objs:
                                        second_verb_objs.extend(find_objects_from_conjunc(second_verb_objs))
                                        for obj in second_verb_objs:
                                            objs_compounds = find_compounds(obj)
                                            svos.append((" ".join(tok.lower_ for tok in second_verb_subs), second_verb.lemma_, " ".join(tok.lower_ for tok in objs_compounds)))
                                else:
                                    #print("objs",objs)
                                    if objs:
                                        rights = [tok for tok in verb.rights]
                                        for tok in rights:
                                            if tok.dep_ in ['dobj','pobj']:
                                                subs.append(tok)
                                            elif tok.pos_ == "ADP" and tok.dep_ == "agent":
                                                for t in tok.rights:
                                                    if t.dep_ == "pobj":
                                                        subs.append(t)
                                if subs:
                                    svos.append((" ".join(tok.lower_ for tok in subs),verb.lemma_, " ".join(tok.lower_ for tok in objs)))
                                else:
                                    svos.append((None, verb.lemma_, " ".join(tok.lower_ for tok in objs)))
                        else:
                            svos.append((None, verb.lemma_, " ".join(tok.lower_ for tok in objs)))
    return svos


# ______________________________________________________________ #
# Create a list of dictionaries, one dictionary for each feature
# with the given-when-then triplets for each scenario

def create_feature_triplets(features):
    features_steps_with_tripl = []
    for i, feature in enumerate(features):
        # Create a dictionary of the feature triplets
        # Keys: background_triplets,
        # given_triplets, when_triplets, then_triplets
        feature_steps = {}
        feature_steps["Feature_nr"] = i+1
        background_triplets = []
        for step in feature["Background"]:
            background_triplets.append(step_svo(step))
        #print("Background triplets: ", background_triplets)
        feature["background_triplets"] = background_triplets
        feature_steps["background_triplets"] = background_triplets
        list_of_scenario_steps = []
        for i, scenario in enumerate(feature["Scenarios"]):
            scenario_steps = {}
            given_triplets = []
            when_triplets = []
            then_triplets = []

            for step in scenario["Given"]:
                given_triplets.append(step_svo(step))

            for step in scenario["When"]:
                when_triplets.append(step_svo(step))

            for step in scenario["Then"]:
                then_triplets.append(step_svo(step))

            scenario["given_triplets"] = given_triplets
            scenario["when_triplets"] = when_triplets
            scenario["then_triplets"] = then_triplets
            #print(f'Scenario {scenario["Scenario"]} with tripletes', scenario)
            scenario_steps["scenario_nr"] = i+1
            scenario_steps["given_triplets"] = given_triplets
            scenario_steps["when_triplets"] = when_triplets
            scenario_steps["then_triplets"] = then_triplets
            list_of_scenario_steps.append(scenario_steps)
            feature_steps["scenario"] = list_of_scenario_steps
        #print(f"Feature {i} triplets: ", list_of_scenario_steps)
        features_steps_with_tripl.append(feature_steps)
        #print("features",features)
        #print(features_steps)
    return features_steps_with_tripl


# _________________________________________________________________ #
# Run the step_svo function with prints of dependencies for each step
# in order to check the outcome of the algorithm

def trial_print_triplets(features):
    for feature in features:
        for scenario in feature["Scenarios"]:
            print(scenario)
            for step in scenario["When"]:
                for tok in step:
                    print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....",
                          [left.text for left in tok.lefts], "....",[right.text for right in tok.rights])
                print("When triplets: ",step_svo(step))

            for step in scenario["Given"]:
                for tok in step:
                    print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....", [left.text for left in tok.lefts], "....",[right.text for right in tok.rights])
                print("Given triplets: ",step_svo(step))

            for step in scenario["Then"]:
                for tok in step:
                    print(tok.text, "....", tok.pos_,"....",tok.dep_, "....",tok.head, "....", [left.text for left in tok.lefts], "....",[right.text for right in tok.rights])
                print("Then triplets: ", step_svo(step))


# ___________________________________________________ #
# Run preprocessing, create_feature_triplets and trial_print_triplets
# with one project text file as input

#with open('/Users/home/Desktop/bdd_testing.txt') as v:
 #   text = v.read()
#print(f"text_file:",text)
#list_of_features, features_steps = preprocessing(text)
#print("list_of_features: ", list_of_features)
#print("features_steps: ", features_steps)
#features_steps_with_tripl = create_feature_triplets(features_steps)
#print('features_steps_with_triplets', features_steps_with_tripl)
#trial_print_triplets(features_steps)

