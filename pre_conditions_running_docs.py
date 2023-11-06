
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

nlp = spacy.load("en_core_web_md")
matcher = Matcher(nlp.vocab)

# Separate "|" from prefix and suffix
suffixes = nlp.Defaults.suffixes + [r"\|"]
suffix_regex = spacy.util.compile_suffix_regex(suffixes)
nlp.tokenizer.suffix_search = suffix_regex.search

prefixes = nlp.Defaults.prefixes + [r"\|"]
prefix_regex = spacy.util.compile_prefix_regex(prefixes)
nlp.tokenizer.prefix_search = prefix_regex.search


# Create data_type match
# @Language.component("data_type_retokenise")
# def data_type_retokenise(doc):
# matcher = Matcher(nlp.vocab)
# pattern = [{"TEXT": "|"}, {"IS_ALPHA": True, "OP": "+"}, {"TEXT": "|"}]
# matcher.add("data_type", [pattern])
# matches = matcher(doc)

# print("Before:", [token.text for token in doc])

# with doc.retokenize() as retokenizer:
# for match_id, start, end in matches:
# retokenizer.merge(doc[start:end])
# print("After:", [token.text for token in doc])
# return doc


# nlp.add_pipe("data_type_retokenise", first=True)
# print(nlp.pipe_names)

def dep_display(doc, i):
    svg = displacy.render(doc, style="dep")
    file_name = "line" + str(i) + ".svg"
    output_path = Path("/Users/home/Desktop/Dep_graphs/" + file_name)
    output_path.open("w", encoding="utf-8").write(svg)
    return svg


with open('/Users/home/Desktop/UseReqInitial/7.txt') as v:
    text = v.read()
# print(text)
text1 = """Feature: Orders
    Scenario: view unpaid order
    Given that I have ordered
    When I request an order by it`s id
Then I can view the details of the order
| product names | [`Chair`,`Keyboard`,`Dell Laptop`] |
| product descriptions | [`Made in Stockholm`,`Mechanical`,`IPS Screen`] | 
And I should be prompted to submit a payment
And I have the option to review the order
And I have the option to cancel the order
And I have the option to update the order
Scenario: view paid order
Given that I have ordered
When I request an order by it`s id
Then I can view the details of the order
| product names | [`Chair`,`Keyboard`,`Dell Laptop`]|
| product descriptions | [`Made in Stockholm`,`Mechanical`,`IPS Screen`] | 
And I have the option to review the order"""

# Split the Feature text in lines
#text1 = text1.split(sep='\n')
#print(text1)

# Split the Feature text in lines
text = text.split(sep='\n')
print(text)
single_spaces_text = []

# Remove all blancs from feature file lines
for line in text:
    single_spaces_line = ' '.join(line.split())
    single_spaces_text.append(single_spaces_line)
print(f'Joined :{single_spaces_text}')
print(type(single_spaces_text))

# Remove all void lines from the feature file
single_spaces_text = [str for str in single_spaces_text if str]

print(single_spaces_text)

# for i in range(len(single_spaces_text)):
# print(f'Index:  {i} {single_spaces_text[i]}')

# Create a list of docs - each doc is a line of the feature file
docs = list(nlp.pipe(single_spaces_text))
# print(docs)
# print(docs.__len__())
# for i in range(docs.__len__()):
# print(docs[i].text)


# Those are the guerkin keywords
keywords = ["Rule", "Scenario Outline", "Scenario Template", "Given", "When", "Then", "And", "But"]
keywords_withpunc = ["Feature", "Background", "Example", "Examples", "Scenario", "Scenarios", ]

# Separate the features of a project in different lists of docs
nr_of_features = 0
for doc in docs:
    if doc[0].text == "Feature":
        nr_of_features += 1
print(f"Number of Features: {nr_of_features}")

features = [[] for i in range(nr_of_features)]
print(features)
count = -1
for i, doc in enumerate(docs):
    if doc[0].text == "Feature":
        count += 1
        if count >= nr_of_features:
            break
        else:
            features[count].append(doc)
    if doc[0].text != "Feature":
        features[count].append(doc)
        continue

# Separate the scenarios of each feature
# and create a list of all the features, each element of the list a dictionary with three keys
# key Feature, value the count of the feature in the project
# key Background, value a list of the background steps
# key scenarios, value a list of all the scenarios in the feature

scenario_steps = False
background_steps = False
list_of_features = []

for ind, feature in enumerate(features):
    print(f'Feature {ind}:', feature[0][2:].text) # There is ":" after the keyword
    nr_of_scenarios = 0
    features_dict = {}
    for doc in feature:
        if doc[0].text == "Scenario":
            nr_of_scenarios += 1
    print(f"Number of Scenarios: {nr_of_scenarios}")

    scenarios = [[] for i in range(nr_of_scenarios)]
    print(scenarios)

    count = -1
    background = []
    for i, doc in enumerate(feature):
        print(i, doc)
        if i == 0:
            continue
        if doc[0].text == "Background":
            scenario_steps = False
            background_steps = True
        if doc[0].text == "Scenario":
            scenario_steps = True
            background_steps = False
            count += 1
            if count >= nr_of_scenarios:
                break
            else:
                scenarios[count].append(doc)
                # print(scenarios[count])
        if doc[0].text != "Scenario" and scenario_steps:
            scenarios[count].append(doc)
            # print(scenarios[count])
        elif doc[0].text not in ["Scenario", "Background"] and background_steps:
            background.append(doc)
            print(background)
            # continue
    features_dict["Feature"] = ind
    features_dict["Background"] = background
    features_dict["Scenarios"] = scenarios
    print(features_dict)
    list_of_features.append(features_dict)
    print("List of Features:", list_of_features)

# Create pre, post conditions and actions lists per scenario, per feature
pre_conditions = []
action_steps = []
actions_preconditions_steps = []
post_conditions = []
given_steps = False
then_steps = False
when_steps = False

for feature in list_of_features:
    for step in feature["Background"]:
        if step[1].text == "that":
            pre_conditions.append(step[2:])
        else:
            pre_conditions.append(step[1:])
    for scenario in feature["Scenarios"]:
        for doc in scenario:
            if doc[0].text == "Given":
                given_steps = True
                when_steps = False
                then_steps = False
                if doc[1].text == "that":
                    pre_conditions.append(doc[2:])
                else:
                    pre_conditions.append(doc[1:])
            if doc[0].text == "When":
                given_steps = False
                when_steps = True
                action_steps.append(doc[1:])
            if doc[0].text == "Then":
                given_steps = False
                when_steps = False
                then_steps = True
                post_conditions.append(doc[1:])
            if doc[0].text in ["And", "But"] and given_steps:
                pre_conditions.append(doc[1:])
            elif doc[0].text in ["And", "But"] and when_steps:
                actions_preconditions_steps.append(doc[1:])
            elif doc[0].text in ["And", "But"] and then_steps:
                post_conditions.append(doc[1:])

# print("Features: ", features)
# print("Scenarios: ", list_of_features)
print("Pre_conditions: ", pre_conditions)
print("Actions: ", action_steps)
# print('Actions_pre_conditions:', actions_preconditions_steps)
#print("Post_conditions: ",post_conditions)


# Let's parse the actions

actors = []
actions = []
objects = []

i = -1
for doc in action_steps:
    i += 1
    print(f'action {i}')
    for tok in doc:
        print(tok.text, "-->", tok.dep_, "-->", tok.pos_, "-->", tok.head.text, "-->", tok.head.pos_, \
              [child for child in tok.children])
    dep_display(doc, i)

for doc in action_steps:
    for tok in doc:
        if tok.dep_ == "nsubj":
            if tok.text not in actors:
                actors.append(tok.text)
        if tok.pos_ == 'VERB' and tok.head.pos_ == 'VERB' and tok.dep_ == 'xcomp':
            actions.append(tok.text)
        if tok.pos_ == 'VERB' and tok.dep_ == 'ROOT':
            verb_child = [child for child in tok.children if child.pos_ == 'VERB']
            if verb_child != []:
                continue
            elif tok.text not in actions:
                actions.append(tok.text)
        if tok.pos_ == "NOUN" and tok.dep_ == "dobj":
            if tok.text not in objects:
                objects.append(tok.text)

print(actors)
print(actions)
print(objects)

for i,condition in enumerate(pre_conditions):
    print(condition)
    chunks = list(condition.noun_chunks)
    print(f"line {i}", chunks)

    for tok in condition:
        print(tok.text, tok.pos_,tok.dep_,tok.lemma_, tok.head.text, [child.text for child in tok.children])




def log_in_pattern(doc):
    # Create the match patterns user is logged in/i am a logged in user
    pattern1 = [{"LOWER": "user", "OP": "?"}, {"LEMMA": "be"},
                {"LOWER" : {"IN":["loggin", "log", "logged"]}}, {"TEXT": "in"},{"POS":"NOUN","OP":"?"}]
    #pattern2 = [{"LOWER":{"IN":["loggin","logged","log"]}},{"TEXT": "in"}, {"POS": "NOUN"}]


    # Initialize the Matcher and add the patterns
    matcher = Matcher(nlp.vocab)
    matcher.add("log_in_1", [pattern1])
    #matcher.add("log_in_2",[pattern2])

    matches=matcher(doc)

    # Iterate over the matches
    #for match_id, start, end in matches:
        # Print pattern string name and text of matched span
        #print(doc.vocab.strings[match_id], doc[start:end].text)
    if matches:
        return True


def as_pattern (doc):
    # Create the match patterns
    pattern1 = [{"LOWER":"as"}, {"POS": "DET","OP":"?"},{"POS": "NOUN","DEP":"pobj"}]
    pattern2 = [{"POS":"PRON"},{"LEMMA":"be"},{"POS": "DET","OP":"?"},{"POS":"NOUN"}] # I am a user
    pattern3 = [{"POS": "PRON"}, {"LEMMA": "be"}, {"POS": "NOUN", "DEP":"pobj"}]# I am a user

    # Initialize the Matcher and add the patterns
    matcher = Matcher(nlp.vocab)
    matcher.add("as_1",[pattern1])
    matcher.add("as_2",[pattern2])
    matcher.add("as_3", [pattern3])
    matches=matcher(doc)

    # Iterate over the matches
    as_users=[]
    for match_id, start, end in matches:
        # Print pattern string name and text of matched span
        # print(doc[start:end].text)
        as_users.append(doc[start:end][-1])
    #print("as_users: ",as_users)
    return as_users

SUBJECTS=["subj","nsubjpass"]

def svo_pattern(doc):
    subs= [tok for tok in doc if tok.pos_=="NOUN" and tok.dep_ in SUBJECTS]
    if len(subs)>0:
        print("subs: ",subs)
        return subs
    else:
        return []

#users = []
#users_clean=[]
#for condition in pre_conditions:
    #if log_in_pattern(condition):
        #users.append("logged_in_user")
    #for user in as_pattern(condition):
        #(user)
        #users.append(user.text)
    #users.extend(svo_pattern(condition))

#print(users)
#users_clean = list(dict.fromkeys(users))
#print(users_clean)



features = []
for i, feature in enumerate(list_of_features):
    features_i ={}
    feature_nr = i
    list_of_scenarios=[]
    background = []
    for step in feature["Background"]:
        if step[1].text == "that":
            background.append(step[2:])
        else:
            background.append(step[1:])
    print("pre_conditions:", background)
    for j, scenario in enumerate(feature["Scenarios"]):
        scenario_dict = {}
        scenario_nr = j
        given_steps = []
        when_steps = []
        then_steps = []
        given_st = False
        when_st = False
        then_st = False
        for doc in scenario:
            if doc[0].text == "Given":
                given_st = True
                when_st = False
                then_st = False
                if doc[1].text == "that":
                    given_steps.append(doc[2:])
                else:
                    given_steps.append(doc[1:])
            if doc[0].text == "When":
                given_st = False
                when_st = True
                #    # when_pos=i
                when_steps.append(doc[1:])
            if doc[0].text == "Then":
                given_st = False
                when_st = False
                then_st = True
                then_steps.append(doc[1:])
            if doc[0].text in ["And", "But"] and given_st:
                given_steps.append(doc[1:])
            elif doc[0].text in ["And", "But"] and when_st:
                when_steps.append(doc[1:])
            elif doc[0].text in ["And", "But"] and then_st:
                then_steps.append(doc[1:])
        scenario_dict["Scenario"] = j
        scenario_dict["Given"] = given_steps
        scenario_dict["When"] = when_steps
        scenario_dict["Then"] = then_steps
        print("Scenario_dict:", scenario_dict)
        #scenario_dict = {}
        list_of_scenarios.append(scenario_dict)
    features_i["Feature_nr"] = i
    features_i["Background"] = background
    features_i["Scenarios"] = list_of_scenarios
    features.append(features_i)
    print("List of Scenarios:", list_of_scenarios)
print("Features: ", features)  # A list of all features of a project, each feature is a dict
                               # Background (value the background/preconditions of each feature)
                               # and Scenarios (value a list of all scenarios of the feature)
                               # each scenario a dict with four keys: Scenario, Given, When,Then

COMPOUNDS = ["compound"]
def generate_obj_compound(obj):

    obj_compunds = []
    for tok in obj.lefts:
        if tok.dep_ in COMPOUNDS:
            obj_compunds.extend(generate_obj_compound(tok))
    obj_compunds.append(obj)
    print(obj_compunds)
    for tok in obj.rights:
        if tok.dep_ in COMPOUNDS:
            obj_compunds.extend(generate_obj_compound(tok))
        print(obj_compunds)
    return obj_compunds

doc1= nlp(""" The password needs to contain at least one number and one capital letter""")

objs = [tok for tok in doc1 if tok.dep_ in ["dobj","conj"]]
compound_objects=[]
for obj in objs:
    obj_compound= generate_obj_compound(obj)
    compound_objects.append(" ".join(tok.lower_ for tok in obj_compound))
    print(compound_objects)