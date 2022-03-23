import socketio
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from modules.pipeline import Pipeline
import json
import random
from datetime import datetime
import string

chars = string.ascii_letters + string.digits


class KGPServer():


    def __init__(self, logging_file, pipeline, config):

        print('init variables')
        self.logging_file = logging_file
        self.pipeline = pipeline
        self.config = config
        self.prefix_for_type = {0: 'message', 1: 'reload', 2: 'comment', 3: 'save', 4: 'load', 5: 'start'}
        self.dictionary = None

    def analyse_sentence(self, text):
        response = self.pipeline.process(text)

        self.pipeline.metadata['sent_idx'] += 1

        return response


    def create_graph(self, response):
        for s, p, o in self.pipeline.g:
            print((s, p, o))

        graph_strings = []
        for s, p, o in self.pipeline.g:
            idx = str(s).find('entity_')
            if idx > -1:
                s_text = str(s)[idx + 7:]
            else:
                s_text = str(s)
            p_text = str(p)
            idx = str(o).find('entity_')
            if idx > -1:
                o_text = str(o)[idx + 7:]
            else:
                o_text = str(o)

            graph_strings.append(s_text + ", " + p_text + ", " + o_text)

        idx_mapping = {}
        labels = {}
        for s, p, o in self.pipeline.g:
            if s not in idx_mapping:
                idx_mapping[s] = len(idx_mapping)
            if idx_mapping[s] not in labels:
                labels[idx_mapping[s]] = set()

            if o not in idx_mapping and isinstance(o, BNode):
                idx_mapping[o] = len(idx_mapping)
                if idx_mapping[o] not in labels:
                    labels[idx_mapping[o]] = set()

        edges = []
        for s, p, o in self.pipeline.g:
            if isinstance(o, URIRef) and 'entity' in str(o):
                edges.append({"source": idx_mapping[s], "target": idx_mapping[o], "label": str(p).split('/')[-1]})
                label = str(o).split('/')[-1]
                if idx_mapping[o] not in labels:
                    labels[idx_mapping[o]] = set()
                labels[idx_mapping[o]].add(label)
            elif isinstance(o, BNode):
                edges.append({"source": idx_mapping[s], "target": idx_mapping[o], "label": str(p).split('/')[-1]})
            elif isinstance(o, Literal):
                label = str(o)
                if idx_mapping[s] not in labels:
                    labels[idx_mapping[s]] = set()
                labels[idx_mapping[s]].add(label)
            elif isinstance(o, URIRef) and 'entity' not in str(o):
                label = str(o).split('/')[-1]
                labels[idx_mapping[s]].add(label)

            if isinstance(s, URIRef):
                label = str(s).split('/')[-1]
                labels[idx_mapping[s]].add(label)

        print(idx_mapping)
        print(labels)

        nodes = []
        for node in idx_mapping:
            id = idx_mapping[node]
            nodes.append({"name": ', '.join(list(labels[id]))})

        dictionary = {'type': 0,
                      'nodes': nodes,
                      'edges': edges,
                      'response': response,
                      'graph': '<br>'.join(graph_strings)}

        return dictionary

def init_variables():
    config = json.load(open('../config/config.json'))
    g = Graph()
    uid = ''.join([random.choice(chars) for i in range(8)])
    metadata = {"entities": {}, "rel_names":{}, "sent_idx": 0, "uid": uid}
    pipeline = Pipeline(g)
    pipeline.setup(config, metadata)
    date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_")
    logging_file = open(config['loggingpath'] + date_time + uid + ".log", 'w')

    return logging_file, pipeline, config


def emit_setup_message(sio, msg=None):
    if msg:
        msg['service'] = "kgp"
        sio.emit('service_setup_response_server', msg)
    else:
        sio.emit('service_setup_response_server', {"service": "kgp"})

logging_file, pipeline, config = init_variables()
server = KGPServer(logging_file, pipeline, config)



sio = socketio.Client()
sio.connect('http://localhost:3000')
print('my sid is', sio.sid)

# emit setup message
emit_setup_message(sio)

@sio.on('client_message')
def on_message(msg):
    print('I received a message!')
    print(msg)

    messages = msg['messages']

    responses = []
    for message_dict in messages:
        message = message_dict['message']
        messageId = message_dict['messageId']
        response = server.analyse_sentence(message)
        graph_dictionary = server.create_graph(response)
        responses.append({"kgp_graph_dictionary": graph_dictionary, "messageId": messageId, "message": "this is a response"})

    msg['service'] = "kgp"
    msg['responses'] = responses

    print("My response: ")
    print(msg)

    sio.emit('server_response', msg)

@sio.on('service_setup')
def on_message(msg):
    print('I received a setup message!')
    #I'm working, therefore we can reply here.
    emit_setup_message(sio, msg)




