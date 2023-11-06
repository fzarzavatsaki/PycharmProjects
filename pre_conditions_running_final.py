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


def dep_display(doc, i):
    svg = displacy.render(doc, style="dep")
    file_name = "line" + str(i) + ".svg"
    output_path = Path("/Users/home/Desktop/Dep_graphs/" + file_name)
    output_path.open("w", encoding="utf-8").write(svg)
    return svg


with open('/Users/home/Desktop/74_new.txt') as v:
    text = v.read()
# print(text)

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
keywords_withpunc = ["Feature", "Background", "Example", "Examples", "Scenario", "Scenarios"]

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
            # print(background)
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
# print("Pre_conditions: ", pre_conditions)
# print("Actions: ", action_steps)
# print('Actions_pre_conditions:', actions_preconditions_steps)
# print("Post_conditions: ",post_conditions)

# ______________________________________#
# Let's parse the actions

actors = []
actions = []
objects = []

i = -1
for doc in action_steps:
    i += 1
    #print(f'action {i}')
    #for tok in doc:
        #print(tok.text, "-->", tok.dep_, "-->", tok.pos_, "-->", tok.head.text, "-->", tok.head.pos_, \
              #[child for child in tok.children])
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

print("Actors: ", actors)
print("Actions: ",actions)
print("Objects: ", objects)

#for i,condition in enumerate(pre_conditions):
    #print(condition)
    #chunks = list(condition.noun_chunks)
    #print(f"line {i}", chunks)

    #for tok in condition:
        #print(tok.text, tok.pos_,tok.dep_,tok.lemma_, tok.head.text, [child.text for child in tok.children])

# ________________________________________________________ #
# Create dictionary with features of a project, and the given, when, then steps of each scenario of each feature #

features = []
for i, feature in enumerate(list_of_features):
    features_i = {}
    feature_nr = i
    list_of_scenarios = []
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
                # when_pos=i
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
        print(scenario_dict)
        #scenario_dict = {}
        list_of_scenarios.append(scenario_dict)
    features_i["Feature_nr"] = i
    features_i["Background"] = background
    features_i["Scenarios"] = list_of_scenarios
    features.append(features_i)
    print("List of Scenarios:", list_of_scenarios)
print("Features: ", features)  # A list of all features of a project, each feature is a dict with keys
                               # "Background" (value the background/preconditions of each feature)
                               # and "Scenarios" (value a list of all scenarios of the feature)
                               # each scenario a dict with four keys: "Scenario", "Given", "When","Then"


