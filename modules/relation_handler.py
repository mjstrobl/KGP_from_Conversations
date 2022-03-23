from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from stanza.server import CoreNLPClient
from pathlib import Path
import json

SCHEMA_ORG_NAMESPACE = "http://schema.org/"
SCHEMA_ORG = Namespace(SCHEMA_ORG_NAMESPACE)



class RelationHandler():

    def __init__(self, relations, client, annotators, props):
        self.relations = relations
        self.annotators = annotators
        self.props = props
        self.client = client
        self.relation_patterns_semgrex = {}
        self.relation_patterns_tokensregex = {}
        for relation in self.relations:
            file = Path('../rules/edges/semgrex/' + relation + '.json')
            if file.is_file():
                patterns_semgrex = json.load(open('../rules/edges/semgrex/' + relation + '.json'))
                self.relation_patterns_semgrex[relation] = patterns_semgrex
            file = Path('../rules/edges/tokensregex/' + relation + '.json')
            if file.is_file():
                patterns_tokensregex = json.load(open('../rules/edges/tokensregex/' + relation + '.json'))
                self.relation_patterns_tokensregex[relation] = patterns_tokensregex

    def find_semgrex_relations(self, original_sentence, entity_mentions_index, g, result, found_relations, response):
        for relation in self.relation_patterns_semgrex:
            for rule in self.relation_patterns_semgrex[relation]:
                pattern = rule['pattern']
                comment = rule['comment']
                print(pattern)
                matches = self.client.semgrex(original_sentence, pattern, properties=self.props,annotators=self.annotators)
                print(matches)

                for i, sent in enumerate(result.sentence):
                    sentence = matches["sentences"][i]
                    if sentence['length'] > 0:
                        print('sentence')
                        print(sentence)
                        for j in range(sentence['length']):
                            match = sentence[str(j)]
                            print('match')
                            print(match)
                            print(entity_mentions_index)
                            object_index = match["$object"]["begin"]
                            subject_index = match["$subject"]["begin"]
                            if object_index in entity_mentions_index and subject_index in entity_mentions_index and str(subject_index) + "_" + str(object_index) + "_" + relation not in found_relations:
                                subject = entity_mentions_index[subject_index]
                                object = entity_mentions_index[object_index]

                                arguments = self.relations[relation]['arguments']
                                subject_type = URIRef(SCHEMA_ORG_NAMESPACE + arguments[0])
                                object_type = URIRef(SCHEMA_ORG_NAMESPACE + arguments[1])

                                for s, p, o in g:
                                    print((s, p, o))

                                print("subject")
                                print(subject)
                                print("object")
                                print(object)
                                print("2 subject type")
                                print(subject_type)
                                print("2 object type")
                                print(object_type)

                                if (subject, URIRef("http://schema.org/type"), subject_type) in g and (object, URIRef("http://schema.org/type"), object_type) in g:
                                    g.add((subject, URIRef(SCHEMA_ORG_NAMESPACE + relation), object))

                                    print("subject: " + str(subject_index))
                                    print('object: ' + str(object_index))

                                    subject_text = match["$subject"]["text"]
                                    object_text = match["$object"]["text"]

                                    response.append(subject_text + " -> " + relation + " -> " + object_text)
                                else:
                                    print("subject or object type not in graph")

    def find_tokensregex_relations(self,original_sentence, entity_mentions_index, g, result, found_relations, response):
        for relation in self.relation_patterns_tokensregex:
            for rule in self.relation_patterns_tokensregex[relation]:
                pattern = rule['pattern']
                comment = rule['comment']
                print(pattern)
                matches = self.client.tokensregex(original_sentence, pattern, properties=self.props,annotators=self.annotators)
                print(matches)

                for i, sent in enumerate(result.sentence):
                    sentence = matches["sentences"][i]
                    if sentence['length'] > 0:
                        print('sentence')
                        print(sentence)
                        for j in range(sentence['length']):
                            match = sentence[str(j)]
                            print('match')
                            print(match)
                            print(entity_mentions_index)

                            subject_index = match["1"]["begin"]
                            object_index = match["2"]["begin"]

                            if object_index in entity_mentions_index and subject_index in entity_mentions_index:
                                subject = entity_mentions_index[subject_index]
                                object = entity_mentions_index[object_index]

                                arguments = self.relations[relation]['arguments']
                                subject_type = URIRef(SCHEMA_ORG_NAMESPACE + arguments[0])
                                object_type = URIRef(SCHEMA_ORG_NAMESPACE + arguments[1])

                                print("1 subject type")
                                print(subject_type)
                                print("1 object type")
                                print(object_type)

                                if (subject,URIRef("http://schema.org/type"),subject_type) in g and (object,URIRef("http://schema.org/type"),object_type) in g:

                                    g.add((subject, URIRef(SCHEMA_ORG_NAMESPACE + relation), object))

                                    print("subject: " + str(subject_index))
                                    print('object: ' + str(object_index))

                                    subject_text = match["1"]["text"]
                                    object_text = match["2"]["text"]

                                    response.append(subject_text + " -> " + relation + " -> " + object_text)

                                    found_relations.add(str(subject_index) + "_" + str(object_index) + "_" + relation)
                                else:
                                    print("subject or object type not in graph")



    def process_relations(self, original_sentence, entity_mentions_index, g, result):
        response = []
        found_relations = set()
        self.find_tokensregex_relations(original_sentence, entity_mentions_index, g, result, found_relations, response)
        self.find_semgrex_relations(original_sentence, entity_mentions_index, g, result, found_relations, response)

        return response
