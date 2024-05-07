import spacy
import os
from spacy import displacy
from pathlib import Path
from spacy.matcher import Matcher


nlp = spacy.load("en_core_web_lg")
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


def preprocessing(text):
    # Split the Feature text in lines
    feature_text = text.split(sep='\n')
    #print(text)
    single_spaces_text = []

    # Remove all blanks from feature file lines
    for line in feature_text:
        single_spaces_line = ' '.join(line.split())
        single_spaces_text.append(single_spaces_line)
    #print(f'Joined :{single_spaces_text}')
    #print(type(single_spaces_text))

    # Remove all void lines from the feature file
    single_spaces_text = [str for str in single_spaces_text if str]
    #print(single_spaces_text)

    # for i in range(len(single_spaces_text)):
    # print(f'Index:  {i} {single_spaces_text[i]}')

    # _________________________________________________________ #
    # Create a list of docs - each doc is a line of the feature #

    docs = list(nlp.pipe(single_spaces_text))
    # print(docs)
    # print(docs.__len__())
    # for i in range(docs.__len__()):
    # print(docs[i].text)

    # _______________________________________________________________________ #
    # Those are the Gherkin keywords and the Gherkin keywords followed by ":" #

    keywords = ["rule", "scenario outline", "scenario template", "given", "when", "then", "and", "but", "|", "*"]
    keywords_with_punc = ["feature", "background", "example", "examples", "scenario", "scenarios", "rule",
                          "scenario outline"]

    # ____________________________________________________________ #
    # Count the features in a project
    # If keyword features is not placed in the beginning of a line
    # the feature is not counted or processed

    nr_of_features = 0
    for doc in docs:
        if doc[0].text.lower() == "feature":
            nr_of_features += 1
    print(f"Number of Features: {nr_of_features}")

    # ________________________________________________________ #
    # Create a list of all the features named 'features'
    # Each item of the list is a list of the lines of a feature
    # This way in 'features' we have stored all the information
    # of the Gherkin user stories in the UseReq files

    list_of_features = []

    if nr_of_features:
        features = [[] for i in range(nr_of_features)]
        #print(features)
        count = -1
        for i, doc in enumerate(docs):
            if doc[0].text.lower() == "feature":
                count += 1
                if count >= nr_of_features:
                    break
                else:
                    features[count].append(doc)
            if doc[0].text.lower() not in keywords and doc[0].text.lower() not in keywords_with_punc:
                continue
            elif doc[0].text.lower() != "feature":
                features[count].append(doc)

        # ___________________________________________________________________ #
        # Separate the scenarios of each feature
        # and create a list of all the features 'list_of_features',
        # each element of the list a dictionary with four keys
        # key Feature_ind, value the count of the feature in the project
        # key Feature_title, value the title listed after the keyword Feature
        # key Background, value a list of the background steps
        # key Scenarios, value a list of all the scenarios in the feature

        scenario_steps = False
        background_steps = False

        for ind, feature in enumerate(features):
            nr_of_scenarios = 0
            features_dict = {}
            for doc in feature:
                if doc[0].text.lower() in ["scenario", "example"]:
                    nr_of_scenarios += 1
            print(f"Number of Scenarios in Feature {ind+1}: {nr_of_scenarios}")

            scenarios = [[] for i in range(nr_of_scenarios)]

            if nr_of_scenarios:
                #print(scenarios)
                count = -1
                background = []
                feature_title = []
                for i, doc in enumerate(feature):
                    #print(i, doc)
                    if i == 0:
                        if doc[1].text == ":":
                            feature_title.append(doc[2:])
                        else:
                            feature_title.append(doc[1:])
                    if doc[0].text.lower() == "background":
                        scenario_steps = False
                        background_steps = True
                    if doc[0].text.lower() in ["scenario", "example"]:
                        scenario_steps = True
                        background_steps = False
                        count += 1
                        if count >= nr_of_scenarios:
                            break
                        else:
                            scenarios[count].append(doc)
                            # print(scenarios[count])
                    if doc[0].text.lower() not in ["scenario", "example"] and scenario_steps:
                        scenarios[count].append(doc)
                    elif doc[0].text.lower() not in ["scenario", "example", "background"] and background_steps:
                        background.append(doc)
                        #print(background)

                features_dict["Feature"] = ind
                features_dict["Title"] = feature_title
                features_dict["Background"] = background
                features_dict["Scenarios"] = scenarios
                #print(features_dict)
                list_of_features.append(features_dict)
                # print("List of Features:", list_of_features)
            else:
                print(f"There are no scenarios in Feature {ind+1}. This is an empty feature.\n")

            # ________________________________________________________ #
            # Create a list of all features of a project "features_steps",
            # each feature is a dictionary with four keys:
            # Feature_nr, Feature_title, Background, Scenarios
            # each scenario a dict with four keys:
            # Scenario, Scenario_title, Given, When, Then
            # We separate the features and the scenarios
            # and the given, when, then steps of each scenario of each feature

        features_steps = []
        for i, feature in enumerate(list_of_features):
            features_i = {}
            list_of_scenarios = []
            background = []
            for step in feature["Background"]:
                if step[1].text == "that":
                    background.append(step[2:])
                else:
                    background.append(step[1:])
            #print("pre_conditions:", background)
            for j, scenario in enumerate(feature["Scenarios"]):
                scenario_dict = {}
                scenario_title = []
                given_steps = []
                when_steps = []
                then_steps = []
                given_st = False
                when_st = False
                then_st = False
                for doc in scenario:
                    if doc[0].text.lower() in ["scenario", "example"]:
                        scenario_title.append(doc[2:])
                    if len(doc) > 1:
                        if doc[0].text.lower() == "given":
                            given_st = True
                            when_st = False
                            then_st = False
                            if doc[1].text.lower() == "that":
                                given_steps.append(doc[2:])
                            else:
                                given_steps.append(doc[1:])
                        if doc[0].text.lower() == "when":
                            given_st = False
                            when_st = True
                            # when_pos=i
                            when_steps.append(doc[1:])
                        if doc[0].text.lower() == "then":
                            given_st = False
                            when_st = False
                            then_st = True
                            then_steps.append(doc[1:])
                        if doc[0].text.lower() in ["and", "but","*"] and given_st:
                            given_steps.append(doc[1:])
                        elif doc[0].text.lower() in ["and", "but","*"] and when_st:
                            when_steps.append(doc[1:])
                        elif doc[0].text.lower() in ["and", "but","*"] and then_st:
                            then_steps.append(doc[1:])
                scenario_dict["Scenario"] = j+1
                scenario_dict["Scenario_title"] = scenario_title
                scenario_dict["Given"] = given_steps
                scenario_dict["When"] = when_steps
                scenario_dict["Then"] = then_steps
                #print(scenario_dict)
                list_of_scenarios.append(scenario_dict)
            features_i["Feature_nr"] = i+1
            features_i["Feature_title"] = feature["Title"]
            features_i["Background"] = background
            features_i["Scenarios"] = list_of_scenarios
            features_steps.append(features_i)

    else:
        features_steps = []
        print("Empty project")

    return list_of_features, features_steps

# ___________________________________________________________ #
# A function to save the precondition steps,
# action steps and post condition steps of the features of a project


def feature_step_conditions(list_of_dictionaries):
    # input argument the list of feature dictionaries "list_of_features"
    # Create pre, post conditions and actions lists per scenario, per feature
    pre_conditions = []
    action_steps = []
    actions_preconditions_steps = []
    post_conditions = []
    given_steps = False
    then_steps = False
    when_steps = False

    for feature in list_of_dictionaries:
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
                    action_steps.append(doc[1:])
                elif doc[0].text in ["And", "But"] and then_steps:
                    post_conditions.append(doc[1:])

    # print("Features: ", features)
    # print("List_of_features: ", list_of_features)
    print("Pre_conditions: ", pre_conditions)
    print("Actions: ", action_steps)
    print("Post_conditions: ",post_conditions)

    # ______________________________________ #
    # Let's parse the actions
    # We can do that for pre_conditions and post-conditions too

    actors = []
    actions = []
    objects = []

    i = -1
    for doc in action_steps:
        i += 1
        # print(f"action {i}")
        # for tok in doc:
        # print(tok.text, "-->", tok.dep_, "-->", tok.pos_, "-->", tok.head.text, "-->", tok.head.pos_, \
        # [child for child in tok.children])
        dep_display(doc, i)

    for doc in action_steps:
        for tok in doc:
            if tok.dep_ == "nsubj":
                if tok.text.lower() not in actors:
                    actors.append(tok.text.lower())
            if tok.pos_ == 'VERB' and tok.head.pos_ == 'VERB' and tok.dep_ == 'xcomp':
                actions.append(tok.lemma_.lower())
            if tok.pos_ == 'VERB' and tok.dep_ == 'ROOT':
                verb_child = [child for child in tok.children if child.pos_ == 'VERB']
                if verb_child:
                    continue
                elif tok.lemma_.lower() not in actions:
                    actions.append(tok.lemma_.lower())
            if tok.pos_ == "NOUN" and tok.dep_ == "dobj":
                if tok.text not in objects:
                    objects.append(tok.text.lower())

    print("Actors: ", actors)
    print("Actions: ", actions)
    print("Objects: ", objects)

    # for i,condition in enumerate(pre_conditions):
    # print(condition)
    # chunks = list(condition.noun_chunks)
    # print(f"line {i}", chunks)

    # for tok in condition:
    # print(tok.text, tok.pos_,tok.dep_,tok.lemma_, tok.head.text, [child.text for child in tok.children])

# _________________________________________________ #
# In order to run preprocessing for a single project

#with open('/Users/home/Desktop/UseReqInitial/3.txt') as v:
    #text = v.read()
#print(text)

#list_of_features, features_steps = preprocessing(text)

#print("List_of_Features: ", list_of_features)
#print("Features_with_steps: ", features_steps)
#for feature in features_steps:
    #print(type(feature), feature)
#feature_step_conditions(list_of_features)


# ______________________________________________ #
# In order to run preprocessing for a body of projects

# Specify the directory containing the text files
file_dir = "/Users/home/Desktop/UseReqInitial"

# A list of all the files in UseReqInitial
files = os.listdir(file_dir)

# Get a list of the filenames
text_files = []
for filename in files:
    if filename.endswith(".txt"):
        text_files.append(filename)

# Sort the list of filenames based on their serial numbers

#print("File names before sorting:", text_files)
text_files.sort(key=lambda x: int(x.split(".")[0]))

# Iterate over each sorted filename
for filename in text_files:
    # Construct the full path to the file
    file_path = os.path.join(file_dir, filename)
    # Open and read the contents of the file
    with open(file_path, encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # Process the text file
    print(f"Project {filename}")
    list_of_features, features_steps = preprocessing(text)
    print("Features with steps:", features_steps)

