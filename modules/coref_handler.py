from pathlib import Path
import json

SPEAKER_COREFERENCES = {"i","me","my","mine"}

class CorefHandler():

    def __init__(self,config,client, annotators, props):
        self.config = config
        self.client = client
        self.annotators = annotators
        self.props = props

        file = Path('../rules/edges/coreferences.json')
        self.coref_patterns = []
        if file.is_file():
            self.coref_patterns = json.load(open('../rules/edges/coreferences.json'))

    def process(self,original_sentence, result, extractions):
        chains = result.corefChain
        chain_dict = dict()
        for index_chain, chain in enumerate(chains):
            chain_dict[index_chain] = {}
            chain_dict[index_chain]['ref'] = ''
            chain_dict[index_chain]['mentions'] = [{'mentionID': mention.mentionID,
                                                    'mentionType': mention.mentionType,
                                                    'number': mention.number,
                                                    'gender': mention.gender,
                                                    'animacy': mention.animacy,
                                                    'beginIndex': mention.beginIndex,
                                                    'endIndex': mention.endIndex,
                                                    'headIndex': mention.headIndex,
                                                    'sentenceIndex': mention.sentenceIndex,
                                                    'position': mention.position,
                                                    'ref': '',
                                                    } for mention in chain.mention]

        start_idx_to_extraction = {}
        current_chain_idx = 0
        for i in range(len(extractions)):
            for j in range(len(extractions[i])):
                start_idx_to_extraction[extractions[i][j]["start"]] = (i, j)
                if extractions[i][j]["word"].lower() in SPEAKER_COREFERENCES:
                    extractions[i][j]["chain_idx"] = current_chain_idx

        current_chain_idx += 1
        for k, v in chain_dict.items():
            # we reserve chain idx = 0 for the speaker
            current_chain_idx += 1

            print('key', k)
            mentions = v['mentions']

            for mention in mentions:
                print(mention)
                head_mention = None
                if mention['headIndex'] in start_idx_to_extraction:
                    head_mention = start_idx_to_extraction[mention['headIndex']]

                if head_mention is not None:
                    tuple = extractions[head_mention[0]][head_mention[1]]
                    if len(tuple) == 4:
                        extractions[head_mention[0]][head_mention[1]]["chain_idx"] = current_chain_idx

        for rule in self.coref_patterns:
            pattern = rule['pattern']
            comment = rule['comment']
            order = rule['order']
            print(pattern)
            matches = self.client.tokensregex(original_sentence, pattern, properties=self.props,annotators=self.annotators)

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

                        subject_end_index = match["1"]["begin"]
                        object_end_index = match["2"]["begin"]

                        if subject_end_index in start_idx_to_extraction and object_end_index in start_idx_to_extraction:

                            subject_extraction = extractions[start_idx_to_extraction[subject_end_index][0]][start_idx_to_extraction[subject_end_index][1]]
                            object_extraction = extractions[start_idx_to_extraction[object_end_index][0]][-1]


                            if 'chain_idx' in subject_extraction:
                                chain_idx = subject_extraction['chain_idx']
                            elif 'chain_idx' in object_extraction:
                                chain_idx = object_extraction['chain_idx']
                            else:
                                chain_idx = current_chain_idx
                                current_chain_idx += 1

                            extractions[start_idx_to_extraction[object_end_index][0]][-1]["chain_idx"] = chain_idx
                            extractions[start_idx_to_extraction[subject_end_index][0]][start_idx_to_extraction[subject_end_index][1]]["chain_idx"] = chain_idx

                            if order == "reverse":
                                temp_subject = extractions[start_idx_to_extraction[subject_end_index][0]]
                                temp_object = extractions[start_idx_to_extraction[object_end_index][0]]

                                extractions[start_idx_to_extraction[subject_end_index][0]] = temp_object
                                extractions[start_idx_to_extraction[object_end_index][0]] = temp_subject









