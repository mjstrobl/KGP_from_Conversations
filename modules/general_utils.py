from rdflib import URIRef, Literal, BNode
import networkx as nx
import matplotlib.pyplot as plt



def visualize_graph(g):
    G = nx.DiGraph()

    idx_mapping = {}
    labels = {}
    for s, p, o in g:
        if s not in idx_mapping:
            G.add_node(len(idx_mapping))
            idx_mapping[s] = len(idx_mapping)

        if o not in idx_mapping and isinstance(o, BNode):
            G.add_node(len(idx_mapping))
            idx_mapping[o] = len(idx_mapping)

        if o not in idx_mapping and "entity_" in o:
            G.add_node(len(idx_mapping))
            idx_mapping[o] = len(idx_mapping)
        if idx_mapping[s] not in labels:
            labels[idx_mapping[s]] = set()

    for s, p, o in g:
        if isinstance(o, URIRef) and 'entity' in str(o):
            G.add_edge(idx_mapping[s], idx_mapping[o])
            G.edges[idx_mapping[s], idx_mapping[o]]['r'] = str(p).split('/')[-1]

            label = str(o).split('/')[-1]
            if idx_mapping[o] not in labels:
                labels[idx_mapping[o]] = set()
            labels[idx_mapping[o]].add(label)
        elif isinstance(o, BNode):
            G.add_edge(idx_mapping[s], idx_mapping[o])
            G.edges[idx_mapping[s], idx_mapping[o]]['r'] = str(p).split('/')[-1]

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

    for id in labels:
        labels[id] = '\n'.join(labels[id])


    print(labels)
    pos = nx.circular_layout(G)

    nx.draw(G, pos, with_labels=False)
    nx.draw_networkx_nodes(G, pos,
                           node_color='w',
                           node_size=500,
                           alpha=0.8)
    nx.draw_networkx_edge_labels(G, pos)
    nx.draw_networkx_labels(G, pos, labels, font_size=12, font_color='r')
    # nx.draw_networkx_labels(G,pos)
    plt.show()