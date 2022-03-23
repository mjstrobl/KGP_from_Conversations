from pathlib import Path
import json


class AttributeHandler:

    def __init__(self, config, client, annotators, props):
        self.config = config
        self.client = client
        self.annotators = annotators
        self.props = props

        filename = '../rules/edges/attributes.json'
        file = Path(filename)
        self.attribute_patterns = []
        if file.is_file():
            self.attribute_patterns = json.load(open(filename))

    def process(self, original_sentence, result, extractions):

        start_idx_to_extraction = {}
        for i in range(len(extractions)):
            for j in range(len(extractions[i])):
                start_idx_to_extraction[extractions[i][j]["start"]] = (i, j)

        response = []

        for rule in self.attribute_patterns:
            pattern = rule['pattern']
            attribute_subject = rule['subject']
            attribute_object = rule['object']
            relation = "<http://schema.org/" + rule['relation'] + '>'
            print(pattern)
            matches = self.client.tokensregex(original_sentence, pattern, properties=self.props,
                                              annotators=self.annotators)

            for i, sent in enumerate(result.sentence):
                sentence = matches["sentences"][i]
                if sentence['length'] > 0:
                    print('sentence')
                    print(sentence)
                    for j in range(sentence['length']):
                        match = sentence[str(j)]
                        print('match')
                        print(match)
                        print(start_idx_to_extraction)

                        subject_begin_index = match[attribute_subject]["begin"]
                        object_begin_index = match[attribute_object]["begin"]

                        if subject_begin_index in start_idx_to_extraction:

                            begin = match[attribute_object]['begin']
                            end = match[attribute_object]['end']
                            word = match[attribute_object]["text"]

                            idxs = start_idx_to_extraction[subject_begin_index]
                            subject = extractions[idxs[0]][idxs[1]]['word']


                            if object_begin_index in start_idx_to_extraction:
                                idxs = start_idx_to_extraction[object_begin_index]
                                extractions[idxs[0]][idxs[1]]['type'] = 'ATTRIBUTIVE'
                                begin = extractions[idxs[0]][idxs[1]]['start']
                                end = extractions[idxs[0]][idxs[1]]['end']
                                word = extractions[idxs[0]][idxs[1]]['word']

                            object = word

                            response.append(subject + ' -> ' + rule['relation'] + ' -> ' + object)

                            idxs = start_idx_to_extraction[subject_begin_index]
                            extractions[idxs[0]][idxs[1]]['attribute'] = {'relation': relation, "word": word, 'idxs': list(range(begin, end))}

        return response
