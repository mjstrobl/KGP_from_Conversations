import threading
import webbrowser
from http.server import HTTPServer,SimpleHTTPRequestHandler

from modules.pipeline import Pipeline

from pathlib import Path
from os import listdir
from os.path import isfile, join
import json
import string
from datetime import datetime

from rdflib import Graph, Namespace, URIRef, Literal, BNode

SCHEMA_ORG = Namespace("http://schema.org/")

FILE = 'frontend.html'
PORT = 8080

chars = string.ascii_letters + string.digits

def MakeHandlerClassFromArgv(logging_file, pipeline, config):
    class TestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):

            print('init variables')
            self.logging_file = logging_file
            self.pipeline = pipeline
            self.config = config
            self.prefix_for_type = {0:'message', 1:'reload', 2:'comment', 3:'save', 4:'load', 5:'start'}
            self.dictionary = None
            super(TestHandler,self).__init__(*args, **kwargs)

        def analyse_sentence(self, text):

            response = self.pipeline.process(text)

            self.pipeline.metadata['sent_idx'] += 1

            return response


        def do_POST(self):
            """Handle a post request by returning the square of the number."""
            length = int(self.headers.get('content-length'))
            data_string = self.rfile.read(length).decode()

            print("got data: " + data_string)

            message_dict = json.loads(data_string)
            type = message_dict['type']
            text = message_dict['text']
            prefix = self.prefix_for_type[type]



            if type == 0:
                # request for graph after sending message.
                response = self.analyse_sentence(text)
                self.create_graph(response)
                json_string = json.dumps(self.dictionary)
                self.send_response_to_client(json_string)
            elif type == 1:
                # request for graph, only reload
                if self.dictionary == None:
                    self.create_graph('Graph reloaded.')
                else:
                    self.dictionary['response'] = 'Graph reloaded.'
                json_string = json.dumps(self.dictionary)
                self.send_response_to_client(json_string)
            elif type == 2:
                # comment sent.
                response_dict = {"type": 1, "response": "Comment received."}
                self.send_response_to_client(json.dumps(response_dict))
            elif type == 3:
                # save graph to file.
                response_dict = {"type": 1, "response": "Graph saved to file."}
                self.send_response_to_client(json.dumps(response_dict))

                date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_")
                graph_output_filename = self.config['graphpath'] + date_time + '.ttl'

                self.pipeline.g.serialize(destination=graph_output_filename, format='turtle')
                with open(self.config['metadatapath'] + date_time + '.json','w') as f:
                    json.dump(self.pipeline.metadata, f)

            elif type == 4:
                # load graph from file and send back.

                graph_files = [f for f in listdir(self.config['graphpath']) if isfile(join(self.config['graphpath'], f))]

                graph_files.sort()

                if len(graph_files) > 0:
                    latest_graph_file = graph_files[-1]

                    requested_graph_filename = self.config['graphpath'] + latest_graph_file

                    self.pipeline.g = Graph()
                    self.pipeline.g.parse(requested_graph_filename, format="ttl")
                    self.pipeline.metadata = json.load(open(config['metadatapath'] + latest_graph_file[:-4] + '.json'))

                    response = "Graph loaded from file."
                    self.create_graph(response)
                    json_string = json.dumps(self.dictionary)
                    self.send_response_to_client(json_string)

                    self.logging_file = open(config['loggingpath'] + datetime.now().strftime("%m_%d_%Y_%H_%M_%S_") + ".log", 'w')
                else:
                    response_dict = {"type": 0, "response": "No Graph file available."}
                    self.send_response_to_client(json.dumps(response_dict))

            date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            self.logging_file.write(prefix + "\t" + date_time + '\t' + text + "\n")

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
                    o_text = str(o)[idx+7:]
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
                elif isinstance(o,URIRef) and 'entity' not in str(o):
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

            self.dictionary = {'type':0,
                          'nodes': nodes,
                          'edges': edges,
                          'response':response,
                          'graph': '<br>'.join(graph_strings)}

        def send_response_to_client(self, message):
            self.send_response(200)
            self.send_header('Content-Type', 'application/xml')
            self.end_headers()

            self.wfile.write(str(message).encode())

    return TestHandler

def init_variables():
    config = json.load(open('../config/config.json'))
    g = Graph()
    metadata = {"rel_names": {}, "entities": {}, "sent_idx": 0}
    pipeline = Pipeline(g)
    pipeline.setup(config, metadata)
    date_time = datetime.now().strftime("%m_%d_%Y_%H_%M_%S_")
    logging_file = open(config['loggingpath'] + date_time + ".log", 'w')

    return logging_file, pipeline, config


def open_browser():
    """Start a browser after waiting for half a second."""
    def _open_browser():
        webbrowser.open('http://localhost:%s/%s' % (PORT, FILE))
    thread = threading.Timer(0.5, _open_browser)
    thread.start()

def start_server(logging_file, pipeline, config):
    """Start the server."""

    print("start server.")
    server_address = ("", PORT)

    HandlerClass = MakeHandlerClassFromArgv(logging_file, pipeline, config)
    server = HTTPServer(server_address, HandlerClass)
    server.serve_forever()

if __name__ == "__main__":
    logging_file, pipeline, config = init_variables()
    open_browser()
    start_server(logging_file, pipeline, config)
