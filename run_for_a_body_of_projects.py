import spacy
import os
from preprocessing import preprocessing

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

text_files.sort(key=lambda x: int(x.split(".")[0]))

# Iterate over each sorted filename
for filename in text_files:
    # Construct the full path to the file
    file_path = os.path.join(file_dir, filename)

    # Open and read the contents of the file
    with open(file_path, encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # Process the text file
    print(f"Project {filename}...")
    list_of_features, features_steps = preprocessing(text)
    print("Features with steps:", features_steps)

