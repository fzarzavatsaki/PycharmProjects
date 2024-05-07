import json
import codecs
import os

# Open the json file and read it as a string and asign it to the variable fileData
# then parse the string into a list named data
with open('/Users/home/Desktop/DIPLOMATIKH/useReq_file/projects.json', "r") as f:
    fileData = f.read()
data = json.loads(fileData)
print(type(data))
print(data.__len__())

# Test to look into the type of data in "data" file
# "data" is a list of projects (dictionaries)
d = data[14]
print("d", d)
#print(json.dumps(d, indent=2))Ω
print("d.keys", d.keys()) # Each project dict has these keys :tags,requirments,stories,_id, name, description,files
print(d["stories"]) # The Gherkin file of a project
print(type(d["stories"])) #The list of features(dictionaries)
print(len(d['stories'])) #The nr of features in a project
for i in range(0,len(d['stories'])):
    print(d['stories'][i])
f = d['stories'][0]
print("f: ", f)
print(type(f)) # Feature dictionary with keys: rating, requirments, _id, title, text, createdAt, updatedAt, project, seq
print("f.keys", f.keys())
#print(f["text"])

# Now I know how this json file is built

# Extract Gherkin project files
for i in range(0, data.__len__()):
    project = data[i]
    f = codecs.open(f"/Users/home/Desktop/UseReqInitial/{i+1}.txt", "w", "utf-8")
    for story in project['stories']:
        #print(story['text'])
        #f.write(story["title"]) #feature title
        #f.write('\n')
        f.write(story["text"]) # The feature text
        f.write('\n')
    f.close()


# Extract the names
f = codecs.open(f"/Users/home/Desktop/UseReqTitles.txt", "w", "utf-8")
for i in range(0, data.__len__()):
    project = data[i]
    f.write(project['name'])
    f.write('\n')
    print(i, project["name"])