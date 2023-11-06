import spacy
import textacy
from textacy import extract


about_talk_text = ('the user should be able to update an event')
pattern = [[{"POS":"VERB","OP":"?"},{"POS":"ADV","OP":"*"},{"POS":"VERB","OP":"+"}],[{"LEMMA":"be"},{"LEMMA":"log"},{"ORTH":"in"}],
           [{"LEMMA":"be"},{"POS":"ADJ","DEP": "acomp"}]]
pattern2 = [{"LOWER":"should"},{"LEMMA":"be","OP":"?"},{"LOWER":"able", "OP":"?"},{"POS":"PART", "OP":"?"},{"POS":"VERB"}]
pattern3=[{"LEMMA":"be"},{"POS":"VERB","OP":"?"}]

doc = textacy.make_spacy_doc(about_talk_text,lang='en_core_web_sm')
verb_phrases = textacy.extract.token_matches(doc, pattern)
verb_phrases2 = textacy.extract.token_matches(doc, pattern2)
verb_phrases3 = textacy.extract.token_matches(doc, pattern3)
#print(verb_phrases) a generator
# Print all Verb Phrases
doc_verb=[]
doc_obj=[]
for chunk in verb_phrases2:
    print("verb phrase: ",chunk.text)
    for word in chunk:
        for tok in word.lefts:
            print("left" ,tok.text)
            if tok.dep_ in ["subj","nsubjpass","nsubj"]:
                print("subj",tok.text)
        if word.pos_ == "VERB" and word.dep_ == "xcomp":
            doc_verb.append(word.text)
            print("verbs: ",doc_verb)
            for tok in word.rights:
                if tok.dep_ == "dobj":
                    doc_obj.append(tok.text)
                    print("objects: ",doc_obj)

# Extract Noun Phrase to explain what nouns are involved
for chunk in doc.noun_chunks:
    print("noun_chunk",chunk)

print(list(extract.noun_chunks(doc, drop_determiners=True)))

svos= list(extract.subject_verb_object_triples(doc))
print("svos: ",svos)
#print(svos[0][1])


# Getting multiple subjects from a passive sentence
nlp=spacy.load("en_core_web_sm")
each_sentence3 = "John and Jenny were accused of crimes by David"
sent = nlp(each_sentence3)

result = []
subj = None
for word in sent:
    if 'subj' in word.dep_:
        subj = word
        result.append(word)
    elif word.dep_ == 'conj' and word.head == subj:
        result.append(word)
#print(str(result))


