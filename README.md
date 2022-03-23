# KGP from Conversations

## Setup

1. Install requirements from requirements.txt
2. Change path of "tokensregex_ner_rules" to absolute path.
3. Download CoreNLP (https://stanfordnlp.github.io/CoreNLP/download.html) and start server (https://stanfordnlp.github.io/CoreNLP/corenlp-server.html):
   ``java -mx4g -cp "<path to CoreNLP>/*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -timeout 15000 -ner.model 4class -ner.applyFineGrained false -ner.statisticalOnly true
``
4. Create directories ``logging/graphs`` and ``logging/metadata``.

## Start

``python website/server.py``

## Usage

1. Type in messages.
2. Save graph.
3. Load latest graph file.
