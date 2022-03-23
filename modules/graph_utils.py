from rdflib import URIRef, Namespace

SCHEMA_ORG_NAMESPACE = "http://schema.org/"
SCHEMA_ORG = Namespace(SCHEMA_ORG_NAMESPACE)

def create_speaker(g, metadata):
    speaker = URIRef(SCHEMA_ORG_NAMESPACE + "entity_" + str(len(metadata['entities']))).n3()
    metadata['entities'][speaker] = (0, 0)
    run_update(g, ["INSERT DATA { " + speaker + " <http://schema.org/type> <http://schema.org/PERSON> . }", []], {})

    return speaker

def run_query(g, query, arguments):
    for key in query[1]:
        if key not in arguments:
            return []

    query = create_query(query[0], query[1], arguments)
    qres = g.query(query)
    candidates = []
    for row in qres:
        id = '<' + str(row[0]) + '>'
        print('id: ' + id)
        candidates.append((id, 1))

    return candidates

def run_attribute_query(g, query):
    qres = g.query(query)
    words = []
    for row in qres:
        words.append(str(row[0]))

    return words


def run_update(g, query, arguments):
    for key in query[1]:
        if key not in arguments:
            print(key)
            return

    print('run query')
    print(arguments)
    query = create_query(query[0], query[1], arguments)
    g.update(query)


def create_query(query, keys, arguments):
    print('create query')
    print(arguments)
    print(query)
    for key in keys:
        if type(arguments[key]) is str:
            if arguments[key][0] == '<':
                query = query.replace("?" + key + ' ', arguments[key] + ' ')
            else:
                query = query.replace("?" + key + ' ', '\"' + arguments[key] + '\"')
    print(query)
    return query




def set_metadata(metadata,entity_mentions_index,node, entity_idxs):
    for i in range(len(entity_idxs)):
        entity_mentions_index[entity_idxs[i]] = URIRef(node[1:-1])
    metadata['entities'][node] = (metadata['sent_idx'], entity_idxs[0])

    print(metadata)

def create_node(metadata, entity_mentions_index, entity_idxs):
    node = URIRef(SCHEMA_ORG_NAMESPACE + "entity_" + str(len(metadata['entities']))).n3()
    set_metadata(metadata, entity_mentions_index, node, entity_idxs)
    return node

def get_candidates(g, query, arguments):
    print('arguments')
    print(arguments)
    candidates = []
    if 'previous_entities' in arguments:
        new_previous_entities = []
        for tuple in arguments['previous_entities']:
            print(tuple)
            entity = tuple[0]
            arguments['previous_entity'] = entity
            current_candidates = run_query(g, query, arguments)
            candidates.extend(current_candidates)
            while len(new_previous_entities) < len(candidates):
                new_previous_entities.append(tuple)

            #del arguments['previous_entity']


        if len(new_previous_entities) > 0:
            arguments['previous_entities'] = new_previous_entities
        print(arguments)
    else:
        candidates = run_query(g, query, arguments)

    print('found ' + str(len(candidates)) + " candidates.")

    return candidates

'''def ask_for_candidates(g, queries, arguments):
    print('arguments')
    print(arguments)
    candidates = []
    if 'previous_entities' in arguments:
        candidates = arguments['previous_entities']

        for query in queries:
            current_candidates = []
            for tuple in candidates:
                entity = tuple[0]
                arguments['previous_entity'] = entity
                if run_ask(g, query, arguments):
                    current_candidates.extend(entity)
            if len(current_candidates) > 0:
                candidates = current_candidates

        del arguments['previous_entity']

    print('found ' + str(len(candidates)) + " candidates.")

    return candidates'''

'''def run_ask(g, query, arguments):
    for key in query[1]:
        if key not in arguments:
            return False

    query = query[0]

    print(query)
    print(arguments)
    query = create_query(query, arguments)
    print(query)
    qres = g.query(query)
    print('result:')
    print(bool(qres))
    return bool(qres)'''