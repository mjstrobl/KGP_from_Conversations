from rdflib import URIRef
from modules.graph_utils import run_update, create_speaker, get_candidates, create_node, SCHEMA_ORG_NAMESPACE, \
    set_metadata, run_attribute_query


class EntityHandler:

    def __init__(self, relations, queries, g, metadata):
        self.g = g
        self.metadata = metadata
        self.relation_mapper = {}
        self.queries = queries
        for relation in relations:
            arguments = relations[relation]["arguments"]
            if "names" in relations[relation]:
                names = relations[relation]["names"]
                for name in names:
                    self.relation_mapper[name] = {"relation": relation, "inverse": False, "subject": arguments[0],
                                                  "object": arguments[1]}
            if "inverse_names" in relations[relation]:
                inverse_names = relations[relation]["inverse_names"]
                for inverse_name in inverse_names:
                    self.relation_mapper[inverse_name] = {"relation": relation, "inverse": True,
                                                          "subject": relations[relation]["arguments"][1],
                                                          "object": relations[relation]["arguments"][0]}
        self.speaker = create_speaker(g, metadata)

    def filterCandidates(self, candidates, filter):


        yes = set()
        no = set()

        for i in range(len(candidates)):
            candidate = candidates[i]
            if candidate[0] in self.metadata["rel_names"] and filter in self.metadata["rel_names"][candidate[0]]:
                yes.add(i)
            elif candidate[0] in self.metadata["rel_names"] and filter not in self.metadata["rel_names"][candidate[0]]:
                no.add(i)

        new_candidates = []
        for i in range(len(candidates)):
            if i in yes:
                new_candidates.append(candidates[i])

        if len(new_candidates) > 0:
            print("we have new candidates")
            print("old")
            print(candidates)
            candidates = new_candidates
            print("we have new candidates")
            print("new")
            print(candidates)
        else:
            for i in range(len(candidates)):
                if i not in no:
                    new_candidates.append(candidates[i])

            candidates = new_candidates

        return candidates


    def process(self, extractions, entity_mentions_index):
        found_corefs = {0: self.speaker}
        arguments = {}

        response = []

        for extraction in extractions:
            print(found_corefs)
            idx_list = []

            current_response = []

            for i in range(len(extraction)):

                entity = extraction[i]
                print()
                word = entity['word']
                print('word: ' + word)
                type_parts = entity['type'].split('_')
                type = type_parts[0]
                if len(type_parts) > 1:
                    arguments["ner"] = URIRef(SCHEMA_ORG_NAMESPACE + type_parts[-1]).n3()

                arguments["word"] = word

                entity_idxs = list(range(entity['start'], entity['end']))

                if len(idx_list) > 0 and 'entities' in extraction[idx_list[-1]]:
                    arguments['previous_entities'] = extraction[idx_list[-1]]['entities']

                if word in self.relation_mapper:
                    arguments["ner"] = URIRef(SCHEMA_ORG_NAMESPACE + self.relation_mapper[word]["subject"]).n3()
                    arguments["relation"] = URIRef(SCHEMA_ORG_NAMESPACE + self.relation_mapper[word]["relation"]).n3()

                if "RELATION" in type:
                    # we'll send the query with the previous entity.
                    # If there is no previous entity, we will create a new one, but not set the new one to previous_entity.
                    # the previous entity will only be set if there is an entity found.
                    # I would say the relation will be added later, once all entities are figured out.
                    # there has to be a previous entity.
                    idx_list.append(i)
                    query = self.queries[type]["query"]
                    inserts = []

                    if 'chain_idx' in entity and entity['chain_idx'] in found_corefs:
                        print('found coref')
                        candidates = [(found_corefs[entity['chain_idx']], 1)]
                        inserts.append(self.queries[type]["insert"])
                    else:
                        candidates = get_candidates(self.g, query, arguments)

                        candidates = self.filterCandidates(candidates,word)

                        if "attribute" in entity:
                            query = "SELECT ?word WHERE { ?entity ?relation ?word . }"
                            perfect_candidates = []
                            potential_candidates = []

                            for candidate in candidates:
                                new_query = query.replace("?entity", candidate[0])
                                new_query = new_query.replace("?relation", entity["attribute"]["relation"])

                                print("new query")
                                print(new_query)

                                words = run_attribute_query(self.g, new_query)
                                print("words")
                                print(words)

                                if len(words) == 0:
                                    potential_candidates.append(candidate)
                                elif entity["attribute"]["word"] in words:
                                    perfect_candidates.append(candidate)

                            if len(perfect_candidates) > 0:
                                candidates = perfect_candidates
                            elif len(potential_candidates) > 0:
                                candidates = potential_candidates
                            else:
                                candidates = []

                            inserts.append(["INSERT DATA { ?entity ?attribute_relation ?attribute_word ; <http://schema.org/type> ?ner . }",
                                            ["entity", "attribute_relation", "attribute_word", "ner"]])
                            entity['attribute_relation'] = entity["attribute"]["relation"]
                            entity['attribute_word'] = entity["attribute"]["word"]
                            entity_idxs.extend(entity['attribute']['idxs'])
                        if len(candidates) == 0:
                            seen_entities = set()
                            for tuple in arguments['previous_entities']:
                                # TODO: this is a bug, not sure why it happens.
                                if tuple[0] not in seen_entities:
                                    candidates.append((create_node(self.metadata, entity_mentions_index, entity_idxs), 0))
                                    seen_entities.add(tuple[0])
                            inserts.append(self.queries[type]["insert"])
                            current_response.append(entity['word'])


                    print('inserts')
                    print(inserts)
                    entity['entities'] = candidates
                    entity['inserts'] = inserts
                    entity['rel_word'] = word
                    entity['relation'] = URIRef(SCHEMA_ORG_NAMESPACE + self.relation_mapper[word]["relation"]).n3()
                    entity['ner'] = arguments["ner"]
                    entity['previous_entities'] = arguments['previous_entities']
                elif type == "NER":
                    idx_list.append(i)
                    # just look for all entities matching type and name.
                    # again, the previous entity is only set if there was an entity found.
                    query = self.queries[type]["query"]
                    inserts = []

                    if 'chain_idx' in entity and entity['chain_idx'] in found_corefs:
                        print('found coref')
                        candidates = [(found_corefs[entity['chain_idx']], 1)]
                        inserts.append(self.queries[type]["insert"])
                    else:
                        candidates = get_candidates(self.g, query, arguments)
                        if len(candidates) == 0:
                            candidates = [
                                (create_node(self.metadata, entity_mentions_index,
                                             list(range(entity['start'], entity['end']))), 0)]
                            inserts.append(self.queries[type]["insert"])
                            current_response.append(entity['word'])

                        if "attribute" in entity:
                            inserts.append(["INSERT DATA { ?entity ?attribute_relation ?attribute_word . }",
                                            ["entity", "attribute_relation", "attribute_word"]])
                            entity['attribute_relation'] = entity["attribute"]["relation"]
                            entity['attribute_word'] = entity["attribute"]["word"]
                            entity_idxs.extend(entity['attribute']['idxs'])

                    entity['entities'] = candidates
                    entity['inserts'] = inserts
                    entity['ner'] = arguments["ner"]
                    entity['word'] = word

                elif type == "PRP":
                    idx_list.append(i)
                    # here we need to see if there is a coreference entity
                    if 'chain_idx' in entity and entity['chain_idx'] in found_corefs:
                        entity['entities'] = [(found_corefs[entity['chain_idx']], 1)]
                        if "attribute" in entity:
                            inserts = [["INSERT DATA { ?entity ?attribute_relation ?attribute_word . }",
                                        ["entity", "attribute_relation", "attribute_word"]]]
                            entity['attribute_relation'] = entity["attribute"]["relation"]
                            entity['attribute_word'] = entity["attribute"]["word"]
                            entity_idxs.extend(entity['attribute']['idxs'])
                            entity['inserts'] = inserts
                    else:
                        break

            response.append(current_response)

            for i in range(len(idx_list) - 1, 0, -1):
                print(idx_list[i])
                entity = extraction[idx_list[i]]
                candidates = entity['entities']
                if 'previous_entities' in entity:
                    previous_entities = entity['previous_entities']

                    for j in range(len(candidates)):
                        previous_entity = previous_entities[j][0]

                        for k in range(len(extraction[idx_list[i]]['entities'])):
                            if previous_entity == extraction[idx_list[i]]['entities'][k][0]:
                                tuple = (extraction[idx_list[i]]['entities'][k][0],
                                         extraction[idx_list[i]]['entities'][k][1] + candidates[j][1])
                                extraction[idx_list[i]]['entities'][k] = tuple
                                break

            print(idx_list)
            for i in range(len(idx_list)):
                idx = idx_list[i]
                entity = extraction[idx]
                print()
                print(entity)
                if 'entities' in entity:
                    candidates = entity['entities']
                    print(candidates)

                    best_rank = -1
                    best_id = -1
                    for j in range(len(candidates)):
                        rank = candidates[j][1]
                        if rank > best_rank:
                            best_rank = rank
                            best_id = j

                    candidate = candidates[best_id][0]

                    if 'chain_idx' in entity:
                        found_corefs[entity['chain_idx']] = candidate

                    arguments = {}

                    arguments['entity'] = candidate
                    if 'previous_entities' in entity:
                        arguments['previous_entity'] = entity['previous_entities'][best_id][0]
                    print(candidate)

                    set_metadata(self.metadata, entity_mentions_index, candidate,
                                 list(range(entity['start'], entity["end"])))

                    if 'attribute' in entity:
                        idxs = entity['attribute']['idxs']
                        set_metadata(self.metadata, entity_mentions_index, candidate,idxs)


                    if 'rel_word' in entity:
                        if candidate not in self.metadata['rel_names']:
                            self.metadata["rel_names"][candidate] = []

                        self.metadata['rel_names'][candidate].append(entity['rel_word'])

                    if 'inserts' in entity:
                        print(entity)
                        inserts = entity['inserts']
                        for insert in inserts:
                            for key in insert[1]:
                                if key in entity:
                                    arguments[key] = entity[key]

                            run_update(self.g, insert, arguments)

        responses = []

        for i in range(len(response)):
            if len(response[i]) > 0:
                responses.append(' '.join(response[i]))

        print()
        print()
        print()
        print()
        for extraction in extractions:
            for i in range(len(extraction)):
                entity = extraction[i]
                if 'entities' in entity:
                    print(entity['word'])
                    print(entity['entities'])
                    print()

            print()

        return responses
