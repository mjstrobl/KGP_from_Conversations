import json
from rdflib import Graph, Namespace
import string
import random
from modules.general_utils import visualize_graph
from modules.mention_handler import MentionHandler
from modules.attribute_handler import AttributeHandler
from modules.entity_handler import EntityHandler
from modules.relation_handler import RelationHandler
from modules.coref_handler import CorefHandler

SCHEMA_ORG_NAMESPACE = "http://schema.org/"
SCHEMA_ORG = Namespace(SCHEMA_ORG_NAMESPACE)


class Pipeline():

    def __init__(self, g):
        self.g = g

    def setup(self, config, metadata):
        # self.tokenizer = CoreNLPProcessor(config)

        # self.tokenizer.process("test sentence")

        self.mention_handler = MentionHandler(config)
        self.attribute_handler = AttributeHandler(config, self.mention_handler.client, self.mention_handler.annotators,
                                          self.mention_handler.props)
        self.coref_handler = CorefHandler(config, self.mention_handler.client, self.mention_handler.annotators,
                                          self.mention_handler.props)

        relations = json.load(open("../rules/edges/relations.json"))
        queries = json.load(open("../rules/nodes/queries.json"))

        self.g = Graph()
        self.metadata = metadata

        self.entity_handler = EntityHandler(relations, queries, self.g, self.metadata)

        self.relation_handler = RelationHandler(relations, self.mention_handler.client, self.mention_handler.annotators,
                                                self.mention_handler.props)

    def process(self, sentence):
        result, extractions = self.mention_handler.process_sentence(sentence)
        print(*[ent for ent in extractions], sep='\n')
        attribute_response = self.attribute_handler.process(sentence, result, extractions)
        self.coref_handler.process(sentence, result, extractions)
        print(*[ent for ent in extractions], sep='\n')

        entity_mentions_index = {}
        entity_response = self.entity_handler.process(extractions, entity_mentions_index)
        relation_response = self.relation_handler.process_relations(sentence, entity_mentions_index, self.g, result)

        for s, p, o in self.g:
            print((s, p, o))
        #visualize_graph(self.g)

        response = ''
        if len(attribute_response) > 0:
            response += 'Attributes: ' + '<br>'.join(attribute_response) + '<br>'

        if len(entity_response) > 0:
            response += 'Entities: ' + ', '.join(entity_response) + '<br>'

        if len(relation_response) > 0:
            response += 'Relations: ' + '<br>'.join(relation_response) + '<br>'

        return response


if __name__ == "__main__":
    sentence = "John's sister's husband's child Martha Smith and John's sister Sarah live in Edmonton with Sarah's husband. John married Sarah Smith. Sarah Smith was born in Edmonton."
    # sentence = 'John likes poutine.'
    # sentence = "John or his sister live in Edmonton. Her name is Sarah."
    # sentence = "John is my brother. He lives in Edmonton. His sister lives there too and she was born in Calgary."
    # sentence = "Hi, I'm Michael. His sister was born in Santa Barbara and John Miller is married to Sarah Smith. Michael Josef Smith lives in Munich. I eat a bacon sandwich every day."
    # sentence = "John's sister's husband's mother Martha Smith"
    # sentence = "My sister's husband Tony lives in Munich. My sister Sarah's husband was born in Edmonton."
    # sentence = "My sister Sarah lives in Edmonton."
    config = json.load(open('../config/config.json'))

    chars = string.ascii_letters + string.digits

    uid = ''.join([random.choice(chars) for i in range(8)])
    metadata = {"rel_names": {}, "entities": {}, "sent_idx": 0, "uid": uid}

    pipeline = Pipeline(None)
    pipeline.setup(config, metadata)
    pipeline.process(sentence)

    '''tokenizer = CoreNLPProcessor(config)
    tokens = tokenizer.process(sentence)

    print('Tokens:')
    for i in range(len(tokens)):
        print(tokens[i])

    mention_handler = MentionHandler(config)
    tokens = mention_handler.process_sentence(tokens)
    mention_handler.print_tokens(tokens)'''
