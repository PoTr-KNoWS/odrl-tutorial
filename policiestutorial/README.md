# Tutorial on Policies
 
This repo contains a few scripts to be run to validate policies in different languages.
Tutorial: ["Policy Evaluation and Enforcement on the Web with ODRL"](https://potr-knows.github.io/odrl-tutorial) at ESWC 2026

See also the [Slides](https://potr-knows.github.io/odrl-tutorial/presentations/2026.05.10%20Introduction%20to%20policies,%20policy%20languages%20and%20ODRL%20(V%C3%ADctor).pptx)

## Exercise 1

Validate a policy (robots.txt) against the ABNF grammar (grammar.abnf).
If you run the following code, the file will validate. If you write a syntactic bad example, it will not.
```
python validate.py
```

## Exercise 2

Validate a MPEG-21 REL policy (policy.xml) against the XML Schemata (rel-mx.xsd, rel-r.xsd, rel-sx.xsd).
If you run the following code, the file will validate. If you write a syntactic bad example, it will not.

```
python validate.py
```

## Exercise 3

It will simply validate whether a ODRL 2.2 policy is consistent with the OWL ontology

```
python validate.py policy.ttl ODRL2.2.ttl
```

## Exercise 4

It will download SUN's XACML reference implementation, and parse a request and a XACML policy returning a result.

```
run.bat
```
