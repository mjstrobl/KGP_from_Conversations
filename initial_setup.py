import os
import json

def fill_relations(ner_tag,filename):
    relations_dict = json.load(open(filename))
    relations = []
    for relation in relations_dict:
        relation_dict = relations_dict[relation]
        if 'names' in relation_dict:
            for name in relation_dict['names']:
                relations.append("^" + name + "$")

        if 'inverse_names' in relation_dict:
            for name in relation_dict['inverse_names']:
                relations.append("^" + name + "$")


    relations_regex = []
    if len(relations) > 0:
        relations_regex.append('|'.join(relations) + "\t" + ner_tag)

    return relations_regex

relations_regexes = fill_relations("RELATION", "rules/edges/relations.json")

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, 'tmp/regex.ner'), 'w') as f:
    for regex in relations_regexes:
        f.write(regex + '\n')





