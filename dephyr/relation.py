import re
from collections import namedtuple
from itertools import combinations
from queue import Queue
from typing import Iterable, List, Set

Rule = namedtuple('Rule', 'requires creates')


class Relation:
    def __init__(self, elements=None, rules=None):
        self.rules = rules or []  # type: List[Rule]
        self.elements = elements or set()  # type: Set[str]

    def _ingest_lines(self, lines):
        for line_no, line in enumerate(lines):
            if not line or line.startswith('#'):
                continue
            if not self.elements:
                self.elements = {c for c in line.lower() if c.isalpha()}
            else:
                if '->' not in line:
                    raise ValueError('Syntax error in deps file on line {}: "{}"'.format(line_no + 1, line))
                a, b = map(str.strip, line.split('->'))
                requires = {c for c in a.lower() if c.isalpha()}
                creates = {c for c in b.lower() if c.isalpha()}
                self.rules.append(Rule(requires, creates))

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            lines = map(str.strip, f.read().split('\n'))

        self = cls()
        self._ingest_lines(lines)
        return self

    @classmethod
    def from_string(cls, string):
        lines = re.split(r'[;,\n]+', string)
        self = cls()
        self._ingest_lines(lines)
        return self

    def with_rules(self, rules):
        return Relation(self.elements, rules)

    def find_closure(self, items: Iterable) -> set:
        seen = set(items)
        rules = list(self.rules)
        last_seen_len = 0
        while last_seen_len != len(seen):
            last_seen_len = len(seen)
            i = 0
            while i < len(rules):
                rule = rules[i]
                if len(rule.requires & seen) == len(rule.requires):
                    del rules[i]
                    seen.update(rule.creates)
                else:
                    i += 1
        return seen

    @staticmethod
    def _has_sub_key(all_keys, key):
        for n in range(len(key) - 1, -1, -1):
            for sub_key in map(frozenset, combinations(key, n)):
                if sub_key in all_keys:
                    return True
        return False

    def _get_all_sets(self, relation=None):
        elements = relation or self.elements
        for n in range(len(elements)):
            for key in map(frozenset, combinations(elements, n)):
                yield key

    def find_all_keys(self) -> Set[frozenset]:
        all_keys = set()
        for key in self._get_all_sets():
            items = self.find_closure(key)
            if items == self.elements:
                all_keys.add(frozenset(key))
        return all_keys

    def find_candidate_keys(self) -> List[set]:
        all_keys = self.find_all_keys()
        candidate_keys = []
        for key in all_keys:
            if not self._has_sub_key(all_keys, key):
                candidate_keys.append(set(key))
        return candidate_keys

    def find_all_functional_deps(self) -> List[Rule]:
        rules = []
        for key in self._get_all_sets():
            items = self.find_closure(key)
            new_items = items - key
            if new_items:
                rules.append(Rule(set(key), set(new_items)))
        return rules

    def find_bcnf_violators(self) -> Iterable[Rule]:
        all_keys = self.find_all_keys()
        for rule in self.rules:
            if frozenset(rule.requires) not in all_keys:
                yield rule

    def find_3nf_violators(self) -> Iterable[Rule]:
        key_items = set()
        for rule in self.rules:
            key_items.update(rule.requires)
        for rule in self.find_bcnf_violators():
            if rule.creates & key_items != rule.creates:
                yield rule

    def find_minimal_basis(self) -> List[Rule]:
        obj = Relation(self.elements)
        rules = obj.rules
        for rule in self.rules:
            for rhs in rule.creates:
                rules.append(Rule(rule.requires, {rhs}))

        is_modified = True
        while is_modified:
            is_modified = False
            i = 0
            while i < len(rules):
                rule = rules[i]
                if len(rule.requires) > 1:
                    for new_lhs in map(set, combinations(rule.requires, len(rule.requires) - 1)):
                        if obj.find_closure(new_lhs) == obj.find_closure(rule.requires):
                            rule = rules[i] = Rule(new_lhs, rule.creates)
                            is_modified = True
                            break
                orig_closure = obj.find_closure(rule.requires)
                del rules[i]
                if obj.find_closure(rule.requires) == orig_closure:
                    is_modified = True
                else:
                    rules.insert(i, rule)
                    i += 1
        return rules

    def make_minimal(self):
        self.rules = self.find_minimal_basis()

    def compress(self):
        """Combine rules with the same inputs"""
        rules = {}
        for rule in self.rules:
            rules.setdefault(frozenset(rule.requires), set()).update(rule.creates)
        self.rules = []
        for requires, creates in rules.items():
            self.rules.append(Rule(requires, creates))

    def project(self, relation: set) -> 'Relation':
        rules = []
        for lhs in self._get_all_sets(relation):
            items = self.find_closure(lhs)
            rhs = items & relation - lhs
            if rhs:
                rules.append(Rule(lhs, rhs))
        return Relation(relation, rules)

    def decompose_bcnf(self) -> List['Relation']:
        relations = []
        violating_relations = Queue()
        violating_relations.put(self)
        while not violating_relations.empty():
            obj = violating_relations.get()  # type: Relation
            try:
                violator = next(iter(obj.find_bcnf_violators()))
                r1_elems = violator.requires | violator.creates
                r2_elems = obj.elements - violator.creates
                r1 = obj.project(r1_elems)
                r2 = obj.project(r2_elems)
                # r1.make_minimal()
                # r2.make_minimal()
                violating_relations.put(r1)
                violating_relations.put(r2)
            except StopIteration:
                relations.append(obj)
        return relations

    def decompose_3nf(self) -> List['Relation']:
        relations = []
        obj = self.with_rules(self.find_minimal_basis())
        obj.compress()
        for rule in obj.rules:
            relations.append(Relation(rule.requires | rule.creates, [rule]))
        return relations
