"""
validate.py
-----------
Check that policy.ttl is consistent with the ODRL 2.2 ontology (ODRL22.ttl)
using only RDFS / OWL reasoning.

Install once:
    pip install rdflib owlrl

Usage:
    python validate.py policy.ttl ODRL22.ttl
"""

import sys
from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS
import owlrl


def load(path):
    g = Graph()
    try:
        g.parse(path, format="turtle")
    except Exception as e:
        print(f"\n[parse error] {path}")
        # rdflib's BadSyntax usually carries .lines / .why / .args
        for attr in ("lines", "why", "args"):
            val = getattr(e, attr, None)
            if val:
                print(f"  {attr}: {val}")
        # show a snippet around the failing line if we can find it
        lineno = getattr(e, "lines", None)
        if isinstance(lineno, int):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    src = fh.readlines()
                start = max(0, lineno - 3)
                end = min(len(src), lineno + 2)
                print("  context:")
                for i in range(start, end):
                    marker = ">>" if i == lineno else "  "
                    print(f"  {marker} {i+1:4d}: {src[i].rstrip()}")
            except OSError:
                pass
        raise
    return g


def validate(policy_path, ontology_path):
    policy = load(policy_path)
    ontology = load(ontology_path)
    print(f"Policy   triples: {len(policy)}")
    print(f"Ontology triples: {len(ontology)}")

    # Merge and run OWL-RL closure on the combined graph
    merged = policy + ontology
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(merged)

    errors = []

    # 1. owl:disjointWith violations
    for a, _, b in ontology.triples((None, OWL.disjointWith, None)):
        for ind in merged.subjects(RDF.type, a):
            if (ind, RDF.type, b) in merged:
                errors.append(f"{ind} is typed as both {a} and {b} (disjoint).")

    # 2. rdfs:domain violations
    for prop, _, dom in ontology.triples((None, RDFS.domain, None)):
        for s, _, _ in policy.triples((None, prop, None)):
            if (s, RDF.type, dom) not in merged:
                errors.append(f"Domain violation: {s} uses {prop} but is not a {dom}.")

    # 3. rdfs:range violations (only for IRI/bnode objects, skipping literals)
    for prop, _, rng in ontology.triples((None, RDFS.range, None)):
        if rng == RDFS.Literal:
            continue
        for _, _, o in policy.triples((None, prop, None)):
            if hasattr(o, "n3") and not o.n3().startswith('"'):
                if (o, RDF.type, rng) not in merged:
                    errors.append(f"Range violation: {prop} -> {o} is not a {rng}.")

    if not errors:
        print("OK: policy is consistent with the ontology.")
        return 0

    print(f"{len(errors)} issue(s) found:")
    for e in errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate.py policy.ttl ODRL22.ttl")
        sys.exit(2)
    sys.exit(validate(sys.argv[1], sys.argv[2]))