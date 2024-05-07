import spacy
from spacy import displacy
from pathlib import Path
import sys
from spacy.matcher import Matcher


nlp = spacy.load("../venv/lib/python3.9/site-packages/en_core_web_lg")



def dep_display(doc, i):
    svg = displacy.render(doc, style="dep")
    file_name = "line" + str(i) + ".svg"
    output_path = Path("/Users/home/Desktop/Dep_graphs/" + file_name)
    output_path.open("w", encoding="utf-8").write(svg)
    return svg

#  open('/Users/home/Desktop/UseReqInitial/15.txt') as v:
    # text = v.read()
    # print("text:", text)

def preprocessing_with_checks(i, text):
    # Split the Feature text in lines
    feature_text = text.split(sep='\n')
    #print(feature_text)
    single_spaces_text = []

    # Remove all blanks from feature file lines
    for line in feature_text:
        single_spaces_line = ' '.join(line.split())
        single_spaces_text.append(single_spaces_line)
    # print(f'Joined :{single_spaces_text}')
    # print(type(single_spaces_text))

    # Remove all void lines from the feature file
    single_spaces_text = [str for str in single_spaces_text if str]

    # print(single_spaces_text)
    # for i in range(len(single_spaces_text)):
    # print(f'Index:  {i} {single_spaces_text[i]}')

    # Create a list of docs - each doc is a line of the feature file
    docs = list(nlp.pipe(single_spaces_text))

    #print(docs.__len__())
    #for index in range(docs.__len__()):
        #print(docs[index])


    # Those are the guerkin keywords #must check this one here
    keywords = ["rule", "scenario outline", "scenario template", "given", "when", "then", "and", "but", "|", "*"]
    keywords_with_punc = ["feature", "background", "example", "examples", "scenario", "scenarios", "rule",
                          "scenario outline"]

    print(f"\n Project {i}\n","---------\n")

    # Separate the features of a project in different lists of docs
    nr_of_features = 0
    for doc in docs:
        if doc[0].text.lower() == "feature":
            nr_of_features += 1
    print(f"Number of Features: {nr_of_features}")

    list_of_features = []

    if nr_of_features:

        # Create a list of all the features named 'features'
        # Each item of the list is a list of the lines of a feature
        # This way in 'features' we have stored all the information of the guerkin user stories in the usereq files
        features = [[] for ind in range(nr_of_features)]
        #print(features)
        count = -1
        for index, doc in enumerate(docs):
            #print(doc[0].text.lower())
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
        # print("Features: ", features)

        # Separate the scenarios of each feature
        # and create a list of all the features 'list_of_features', each element of the list a dictionary with four keys
        # key Feature_ind, value the count of the feature in the project
        # key Feature_title, value the title listed after the keyword Feature
        # key Background, value a list of the background steps
        # key Scenarios, value a list of all the scenarios in the feature

        scenario_steps = False
        background_steps = False
        #list_of_features = []

        for ind, feature in enumerate(features):
            print(f"\n Feature {ind+1}\n", "____________\n")
            nr_of_scenarios = 0
            features_dict = {}
            background_count = 0

            # checking for the mandatory colon after specific keywords
            for i, doc in enumerate(feature):
                if len(doc) > 0 and doc[0].text.lower() in keywords_with_punc:
                    # print(doc.text)
                    if len(doc) > 1 and doc[1].text == ":":
                        continue
                    else:
                        print(f"There should always be a colon after {doc[0].text} keyword. Please amend accordingly line {i+1}.\n")

            for doc in feature:
                if doc[0].text.lower() == "background":
                    background_count += 1
                if doc[0].text.lower() in ["scenario", "example"]:  # these are interchangeable keywords
                    nr_of_scenarios += 1

            scenarios = [[] for i in range(nr_of_scenarios)]
            # print(scenarios)
            if nr_of_scenarios:
                if background_count > 1:
                    print("Please note there should be only one Background section per Feature. Please reconsider.\n")
                print(f"Number of Scenarios in Feature {ind + 1}: {nr_of_scenarios}\n")
                if nr_of_scenarios > 5:
                    print(f"There are {nr_of_scenarios} scenarios in Feature {ind + 1}. Please reconsider splitting this feature.\n")

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
                        if doc[2:]:
                            print("Please note Background section should not have a title\n")
                    if doc[0].text.lower() in ["scenario", "example"]: # these are interchangeable keywords
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
                        # print(scenarios[count])
                    elif doc[0].text.lower() not in ["scenario", "example", "background"] and background_steps:
                        background.append(doc)
                        # print(background)

                features_dict["Feature"] = ind
                features_dict["Title"] = feature_title
                features_dict["Background"] = background
                features_dict["Scenarios"] = scenarios
                #print(features_dict)
                list_of_features.append(features_dict)
            else:
                # features_dict = {}
                # list_of_features.append(features_dict)
                print(f"There are no scenarios in Feature {ind+1}. This is an empty feature.\n")
        # print("List of Features: ", list_of_features)
        # return features

       # Create dictionary 'features_steps' with all the features of a project, and the given, when, then steps of each scenario of each feature #

        features_steps = []
        for i, feature in enumerate(list_of_features):
            print(f"\n\n Feature {i+1} Steps\n",'_______________', '\n')
            features_i = {}
            list_of_scenarios = []
            background = []
            print(" Check Background Steps\n",'______________________\n')
            background_check(i, feature["Background"])

            for step in feature["Background"]:
                if step[1].text == "that":
                    background.append(step[2:])
                else:
                    background.append(step[1:])
            # print("pre_conditions:", background)
            print("\n\n Check Scenario Steps\n","_______________________\n")
            for j, scenario in enumerate(feature["Scenarios"]):
                print(f"\n Scenario {j+1}\n",'__________\n')
                # Check the scenario steps
                # Count the number of actual steps (without counting tables etc)
                # and issue a warning if the scenario is too long
                steps = step_sequence_count(j, scenario)
                if steps > 10:
                    print(f"There are {len(scenario)} steps in scenario {j+1}. Please reconsider splitting this scenario in two or more\n")
                # Check the similarity of the steps of each scenario and issue a warning
                #  two steps are similar
                step_similarity(scenario)
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
                    if doc[0].text.lower() in ["and", "but", "*"] and given_st:
                        given_steps.append(doc[1:])
                    elif doc[0].text == "|" and given_st:
                        given_steps.append(doc)
                    elif doc[0].text.lower() in ["and", "but", "*"] and when_st:
                        when_steps.append(doc[1:])
                    elif doc[0].text == "|" and when_st:
                        when_steps.append(doc)
                    elif doc[0].text.lower() in ["and", "but", "*"] and then_st:
                        then_steps.append(doc[1:])
                    elif doc[0].text == "|" and then_st:
                        then_steps.append(doc)
                scenario_dict["Scenario_nr"] = j + 1
                scenario_dict["Scenario_title"] = scenario_title
                scenario_dict["Given"] = given_steps
                scenario_dict["When"] = when_steps
                scenario_dict["Then"] = then_steps

                # print(scenario_dict)
                list_of_scenarios.append(scenario_dict)
            # Check if the scenario titles of a feature are similar and issue a warning
            # print(f"\n Check scenario titles\n",'______________________\n')
            print(check_scenario_title(list_of_scenarios))
            features_i["Feature_nr"] = i+1
            features_i["Feature_title"] = feature["Title"]
            features_i["Background"] = background
            features_i["Scenarios"] = list_of_scenarios
            features_steps.append(features_i)
        print("features_steps: ", features_steps)
        print(check_feature_title(features_steps))
    else:                        # This exception is necessary so that the functions that have as argument 'features_steps'
        features_steps = []      # will be able to iterate through the projects even when they are empty of features. Otherwise there would be a NoneType error.
        print(f"There are no Features in Project {i}. This is an empty project.\n")
    # print(check_feature_title(features_steps))
    return features_steps, list_of_features


def check_feature_title(list_of_dictionaries):
    print(f"\n Check Feature Titles\n",'___________________\n')
    feature_titles = []
    titles = []
    for i, item in enumerate(list_of_dictionaries):
        feature_title = item.get("Feature_title")
        feature_titles.append(feature_title)
        print(f"Feature {i+1} title: ", feature_title) # Check if there is a title for each Feature
    titles = [item for title in feature_titles for item in title] # flatten feature_titles which is a list of lists of the feature titles
    print("Feature titles: ", titles,'\n')
    # for title in titles:
    # for doc in title:
    # print(doc.text, doc.has_vector)

    # Checking if there is title for each feature and if the words in the title have vectors, otherwise the code will throw an error
    for i, title_1 in enumerate(titles):
        if not title_1:
            print(f"There is no title in Feature {i+1}\n")
            continue
        if not any(token.has_vector for token in title_1):
            print(f"There are no vectors for the title words of Feature {i+1}. No similarity can be estimated between feature titles. Consider rewriting the title.\n")
            continue
        for j, title_2 in enumerate(titles):
            if i < j and title_2 and any(token.has_vector for token in title_2):
                title_similarity = title_1.similarity(title_2)
                if title_similarity > 0.96:
                    print(title_similarity, f" The title of Feature {i+1} is too similar to the title of Feature {j+1}. Please reconsider.\n" )


def check_scenario_title(list_of_dictionaries):
    print(f"\n Check Scenario Titles\n", '______________________\n')
    scenario_titles = []
    titles = []
    for i, item in enumerate(list_of_dictionaries):
        scenario_title = item.get("Scenario_title")
        scenario_titles.append(scenario_title)
        # print(f"Scenario {i+1} title: ", scenario_title) # Check if there is a title for each Scenario
    titles = [item for title in scenario_titles for item in title] # flatten feature_titles which is a list of lists of the feature titles
    print("Scenario titles: ", titles,'\n')
    # for title in titles:
    # for doc in title:
    # print(doc.text, doc.has_vector)
    
    # Checking if there is title for each scenario and if the words in the title have vectors, otherwise the code will throw an error
    for i, title_1 in enumerate(titles):
        if not title_1:
            print(f"There is no title in Scenario {i+1}.\n")
            continue
        if not any(token.has_vector for token in title_1):
            print(f"There are no vectors for the title words of Scenario {i+1}. No similarity can be estimated between scenario titles. Please check the wording.\n")
            continue
        for j, title_2 in enumerate(titles):
            if i < j and title_2 and any(token.has_vector for token in title_2):
                title_similarity = title_1.similarity(title_2)
                if title_similarity > 0.96:
                    print(title_similarity, f" The title of Scenario {i+1} is too similar to the title of Scenario {j+1}.\n" )


def step_sequence_count(ind, list):
    st_count = 0
    given_when_then_list = []
    for i, doc in enumerate(list):
        if doc[0].text.lower() in ["given", "then", "when", "and", "but", "*"]: # I only count the GWT steps and not data steps
            st_count += 1
        if doc[0].text.lower() in ["given", "when", "then"]: # I only check the GWT steps and not the And But steps
            # I make a list of the first words of the steps in order to check the sequence
            given_when_then_list.append(doc[0].text.lower())
    # print("nr of steps", st_count)
    print(' given-when-then sequence', given_when_then_list,'\n')
    # given_when_then_list_lower = [item.lower() for item in given_when_then_list]
    # The scenario should start with a Given or at least with a When step

    if given_when_then_list and given_when_then_list[0] in ["given", "when"]:
        when_then_count = 0
        if given_when_then_list[0] == "when":
            print("This scenario starts with a When step. Are you sure you have previously sufficiently set up your system with a Given step in Background?\n")
        for i in range(1, len(given_when_then_list)):
            if given_when_then_list[i-1] == "given":
                if given_when_then_list[i] not in ["given", "when"]:
                    print("Given-When_Then sequence not in order. Please check your scenario steps.\n")
            if given_when_then_list[i-1] == "when":
                if given_when_then_list[i] not in ["then", "when"]:
                    print("Given-When_Then sequence not in order. Please check your scenario steps.\n")
                if given_when_then_list[i] == "then":
                    when_then_count += 1
            elif i-1 > 0 and given_when_then_list[i-1] == "then":
                if given_when_then_list[i] not in ["then", "when"]:
                    print("Given-When_Then sequence not in order. Please check your scenario steps.\n")
        if when_then_count > 1:
            print("There are more that one Given When Then step triplets in this scenario.Please reconsider.\n")
        # There should always be a When step in scenario
        if "when" not in given_when_then_list:
            print("There is no When step in your scenario. Please reconsider.\n")
        # A scenario should always end with a Then step
        if given_when_then_list[-1] in ["given", "when"]:
            print("The scenario should always end with a Then step describing the system's response. Please reconsider the scenario steps.\n")
    elif given_when_then_list and given_when_then_list[0] == "then":
        print("A scenario should not start with a Then step. Please check your scenario steps.\n")
    return st_count

def step_similarity(list):
    scenario_steps = []
    for i, doc in enumerate(list):
        if doc[0].text.lower() in ["given", "when", "then", "and", "but", "*"]:
            scenario_steps.append(doc[1:])
    print("\n scenario_steps", scenario_steps,'\n')
    #steps = [item for steps in scenario_steps for item in steps]
    #print("steps", steps)
    if len(list) > 1:
        for i, step_1 in enumerate(scenario_steps):
            if not any(token.has_vector for token in step_1):
                print(f"There are no vectors for the step words of Scenario {i+1}. No similarity can be estimated. Consider rewriting the title.\n")
                continue
            for j, step_2 in enumerate(scenario_steps):
                if i < j and step_2 and any(token.has_vector for token in step_2):
                    step_similarity = step_1.similarity(step_2)
                    if step_similarity > 0.96:
                        print(f"Step {i+1} is the same as Step {j+1}. Please rephrase.\n")


def background_check(i, background_list):
    print("Background_steps",background_list,'\n')
    for step in background_list:
        if step[0].text.lower() not in ["given", "and", "but", "*"]:
            print(f"Only Given steps should be included in Background section of feature {i+1}. Please reconsider.\n")

# ______________________________________________________________ #
# If i want to run the code for all the files in UseReqInitial
# and read the report on the terminal of my IDE

number_of_files = 79
for i in range(1, number_of_files+1):
    with open(f"/Users/home/Desktop/UseReqInitial/{i}.txt") as f:
        text = f.read()
        print("Be reminded that any feature that does not start with the keyword 'feature'\n"
              "can not be processed\nPlease check your feature files\n\n"
              "Keywords should always be in the beginning of a line\n"
              "Keywords inside the lines will be ignored\n=================================")

    result = preprocessing_with_checks(i, text)

    print(f"project {i}", result)


# ________________________________________________________ #
# If I want to get a file with all the reports of all the projects in UseReqInitial

original_stdout = sys.stdout
number_of_files = 79
for i in range(1, number_of_files+1):
    with open(f"/Users/home/Desktop/UseReqInitial/{i}.txt") as f:
        text = f.read()

    output_file_path = f"/Users/home/Desktop/ΔΙΠΛΩΜΑΤΙΚΗ/results/{i}.txt"

    with open(output_file_path, "w") as f:
        sys.stdout = f
        print("\n================================\n")
        print("Be reminded that any feature that does not start \nwith the keyword 'feature' can not be processed.\n"
              "Please check your feature files.\n\n=================================")
        print(f"Project {i}:", preprocessing_with_checks(i, text))

sys.stdout = original_stdout



# ______________________________________________________ #
# Run the code for a single project

#with open(f"/Users/home/Desktop/UseReqInitial/17.txt") as f:
#preprocessing_with_checks(text)



