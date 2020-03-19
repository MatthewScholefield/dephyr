"""A tool to solve for functional dependencies and break up tables into 3NF form"""
from argparse import ArgumentParser
from os.path import isfile
from typing import List

from dephyr.relation import Relation, Rule


def format_key(key: set):
    return ''.join(sorted(key)).upper()


def format_rules(rules: List[Rule]) -> str:
    rule_strings = [
        (len(rule.requires), format_key(rule.requires), format_key(rule.creates))
        for rule in rules
    ]
    return '\n'.join('{} -> {}'.format(a, b) for _, a, b in sorted(rule_strings))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('deps', help='.dep file that has lines like A->BC. Alternatively comma separated string')
    sp = parser.add_subparsers(dest='action')
    sp.required = True
    p = sp.add_parser('closure', help='Find closure for variables')
    p.add_argument('variables', help='Variables to find closure for')
    sp.add_parser('candidates', help='Find candidate keys of relation')
    sp.add_parser('functional_deps', help='Find all functional dependencies of a relation')
    p = sp.add_parser('violators', help='Find rules that violate BCNF / 3NF form')
    p.add_argument('form', choices=['BCNF', '3NF'], help='Form (either BCNF or 3NF)')
    sp.add_parser('basis', help='Find minimal basis of relation')
    p = sp.add_parser('project', help='Project onto a smaller relation')
    p.add_argument('elements', help='Relation to project to (ie. ABDE)')
    p.add_argument('-f', '--full', action='store_true', help='Retain full functional dependencies (don\'t comput minimal basis)')
    p = sp.add_parser('decompose', help='Decompose relation into 3NF or BCNF form')
    p.add_argument('form', choices=['BCNF', '3NF'], help='Form (either BCNF or 3NF)')
    args = parser.parse_args()

    if isfile(args.deps):
        deps = Relation.from_file(args.deps)
    else:
        deps = Relation.from_string(args.deps)

    if args.action == 'closure':
        result = deps.find_closure({c for c in args.variables.lower() if c.isalpha()})
        print(format_key(result))
    elif args.action == 'candidates':
        result = deps.find_candidate_keys()
        print('\n'.join(sorted(map(format_key, result))))
    elif args.action == 'functional_deps':
        result = deps.find_all_functional_deps()
        print(format_rules(result))
    elif args.action == 'violators':
        result = {'BCNF': deps.find_bcnf_violators, '3NF': deps.find_3nf_violators}[args.form]()
        print(format_rules(list(result)))
    elif args.action == 'basis':
        deps.make_minimal()
        deps.compress()
        result = deps.rules
        print(format_rules(result))
    elif args.action == 'project':
        d = deps.project({c for c in args.elements.lower() if c.isalpha()})
        if not args.full:
            d.make_minimal()
        d.compress()
        print(format_rules(d.rules))
    elif args.action == 'decompose':
        relations = {'BCNF': deps.decompose_bcnf, '3NF': deps.decompose_3nf}[args.form]()

        data = []
        for relation in relations:
            data.append((format_key(relation.elements), format_rules(relation.rules)))
        for elements, rules in sorted(data):
            print(elements)
            print(rules)
            print()
    else:
        raise RuntimeError


if __name__ == '__main__':
    main()
