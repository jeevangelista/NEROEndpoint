import json, time
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
'''
Sample:
https://www.ebi.ac.uk/ols/api/search?q=kidney&ontology=uberon,bto
'''
baseURL = "https://www.ebi.ac.uk/ols/api/search?q=%s&ontology=%s&queryFields=label,synonym&exact=true"

'''
Sample JSON:
{
  "term": "Renal Cell Carcinoma Kidney",
  "mapping": {
    "Cell Line": [
      "clo"
    ],
    "Disease": [
      "doid",
      "mondo"
    ],
    "Tissue": [
      "uberon",
      "bto"
    ],
    "Small Molecule": [
      "chebi",
      "dron"
    ]
  }
}
/NERO?query={"term":"Renal Cell Carcinoma Kidney","mapping":{"Cell Line":["clo"],"Disease":["doid","mondo"],"Tissue":["uberon","bto"],"Small Molecule":["chebi","dron"]}}
'''
@app.route('/NERO')
def NERO():
  query_dict = json.loads(request.args["query"])
  term = query_dict["term"]
  split_term = term.split()
  tok_num = len(split_term)
  matches = []

  for i in reversed(range(tok_num)):
    ngrams = get_ngrams(term, i+1)
    match_sets = []
    for n in ngrams:
      # Check if a word in that ngram was previously matched on another ngram
      n_set = set(n.split())
      for m in match_sets:
        if n_set & m:
          continue
      for k,v in query_dict["mapping"].items():
        ontologies = ",".join(v)
        try:
          for tries in range(5):
            res = requests.get(baseURL%(n,ontologies))
            if res.status_code == 200:
              break
            else:
              time.sleep(0.1)
          else:
            return jsonify({"Error": "Can't connect to OLS"})
        except Exception as e:
          raise e
        res_json = res.json()
        if res_json["response"]["numFound"]>0:
          match = res_json["response"]["docs"][0]["label"]
          matches.append({"label": match,
                          "accession": res_json["response"]["docs"][0]["obo_id"],
                          "ngram": n,
                          "type": k})
          match_sets.append(n_set)
          term = term.replace(n, "")
          break


  return jsonify({"query": query_dict, "matches": matches})


def get_ngrams(text, n):
  ngrams = []
  tokens = text.split()
  start = 0
  end = start + n
  while end <= len(tokens):
      token = " ".join(tokens[start:end])
      ngrams.append(token)
      start += 1
      end = start + n
  return ngrams