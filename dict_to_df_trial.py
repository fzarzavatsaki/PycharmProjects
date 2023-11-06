
import pandas as pd
import find_triplets_final
from find_triplets_final import create_feature_triplets
#from pre_conditions_running_final import features
from preprocessing import preprocessing

import csv


#features_steps = create_feature_triplets(features)
#print(isinstance(features_steps, list))


def flatdict(d):
    out = []
    # for key in d:
    # print(key, d[key])
    # for item in d.items():
    # print(item)
    for key, val in d.items():
        if key == 'background_triplets':
            bval = val
        elif key == 'scenario':
            dict_list = val
            #print('dict_list', dict_list)
            #print("shit", out)
            for dict in dict_list:
                # print('dict', dict)
                # print(dict.keys())
                # print(dict.values())
                scen_flattend_dict = {}
                for key, val in dict.items():
                    scen_flattend_dict.update({"background_triplets":bval})
                    #print("double_shit",out)
                    #print("scen_flattend_dict", scen_flattend_dict)
                    #print(key,val)
                    new_key = 'scenario' + '_' + key
                    new_val = val
                    scen_flattend_dict[new_key] = new_val
                #print("scen_flattened_dict", scen_flattend_dict)
                #print("before_out",out)
                out.append(scen_flattend_dict)
                #print("after_out",out)

    return out

numberoffiles = 79
for i in range(1, numberoffiles-1):
    with open(f"/Users/home/Desktop/UseReqInitial/{i}.txt") as f:
        text = f.read()
    # print(text)
    print(f"Project{i}")
    list_of_features, features = preprocessing(text)
    features_steps = create_feature_triplets(features)
    #print('features_steps', features_steps)

    # creating dataframe
    frames = []
    for feature in features_steps:
        flat_feature = flatdict(feature)
        #print("flat_feature", flat_feature)
        df = pd.DataFrame(flat_feature)
        frames.append(df)
    if len(features_steps) > 1:
        final_df = pd.concat(frames, keys=[f"f{j}" for j in range(len(features_steps)-1)])
    elif len(features_steps) == 1:
        final_df = pd.concat(frames, keys=[f'f{0}'])
    else:
        print(f"Project{i} is empty")
        final_df = pd.DataFrame()
    print("final_df",final_df)


    # dataframe to csv
    header = ["background_triplets","scenario_nr", "scenario_given_triplets", "scenario_when_triplets","scenario_then_triplets"]
    try:
        final_df.to_csv(f'/Users/home/Desktop/ProjectsCsvs2/project{i}.csv', mode='w',header=header, index=True )
    except:
        print("Empty project")


