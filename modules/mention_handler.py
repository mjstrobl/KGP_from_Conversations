from stanza.server import CoreNLPClient, StartServer

class MentionHandler():

    def __init__(self, config):

        self.props = {
            'pipelineLanguage': 'en',
            'outputFormat': 'json',
            "ner.model": "edu/stanford/nlp/models/ner/english.conll.4class.distsim.crf.ser.gz",
            "tokensregex.caseInsensitive": 'true',
            "enforceRequirements": "false",
            'annotators': 'coref',
            'coref.algorithm': 'neural',
            "ner.applyFineGrained": 'false',
            "tokensregex.rules": config['tokensregex_ner_rules'],
            "ssplit.isOneSentence": "true"
        }

        self.annotators = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner', 'tokensregex', 'entitymentions', 'parse',
                           'depparse', 'coref']

        self.client = CoreNLPClient(
            annotators=self.annotators,
            properties=self.props,
            timeout=60000, endpoint="http://localhost:9000", start_server=StartServer.DONT_START, memory='16g')

    def process_sentence(self, original_sentence):
        print(original_sentence)
        result = self.client.annotate(original_sentence, output_format='serialized', annotators=self.annotators,
                                      properties=self.props)
        extractions = []
        tokens_extracted_already = set()

        for i, sent in enumerate(result.sentence):
            print("[Sentence {}]".format(i + 1))
            for t in sent.token:
                print("{:12s}\t{:12s}\t{:6s}\t{}".format(t.word, t.lemma, t.pos, t.ner))

            print(*[
                f'entity: {ent.entityMentionText}\ttype: {ent.entityType}\tstart: {ent.tokenStartInSentenceInclusive}\tend: {ent.tokenEndInSentenceExclusive}'
                for ent in sent.mentions], sep='\n')
            print("")
            for ent in sent.mentions:
                start = ent.tokenStartInSentenceInclusive
                end = ent.tokenEndInSentenceExclusive
                entity = ent.entityMentionText
                type = ent.entityType

                if start in tokens_extracted_already:
                    continue
                else:
                    tokens_extracted_already.add(start)

                print(
                    f'entity: {ent.entityMentionText}\ttype: {ent.entityType}\tstart: {ent.tokenStartInSentenceInclusive}\tend: {ent.tokenEndInSentenceExclusive}')

                if len(extractions) == 0:
                    extractions.append([{"start": start, "end": end, "word": entity, "type": type}])
                elif extractions[-1][-1]["end"] == start:
                    extractions[-1].append({"start": start, "end": end, "word": entity, "type": type})
                else:
                    extractions.append([{"start": start, "end": end, "word": entity, "type": type}])

        return result, extractions
