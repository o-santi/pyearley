"""
A simple earley parser implementation

Terminal items are functions of the form str-> bool
Non-terminal symbols are simply strings

To build, simply write a grammar with the rules and
it will (or at least should) do the rest

Written by o_santi
"""


from typing import NewType, Union, Mapping, Any
from collections.abc import Callable
from dataclasses import dataclass
from boltons.setutils import IndexedSet  # type: ignore
from sys import setrecursionlimit
from helpers import withrepr, dump_args

Symbol = NewType("Symbol", str)
Terminal = Callable[[str], bool]


@dataclass(frozen=True)
class Rule:
    """
    Class to represent a grammar Rule

    It has the form str->(str or function)
    where function represents Terminals and
    str represents non-terminals.
    """

    left: str
    right: list[Union[str, Symbol, Terminal]]

    def __repr__(self):
        return f"{self.left} |-> {self.right}"


Grammar = list[Rule]


@dataclass(frozen=True)
class State:
    """
    Class to represent an earley state
    """

    rule_index: int
    prox: int
    start: int

    def __str__(self):
        rule = gramatica[self.rule_index]
        rights = [str(s) for s in rule.right]
        return f"{rule.left}->{' '.join(rights[:self.prox])} •{' '.join(rights[self.prox:])} ({self.start})"

    def __repr__(self):
        return self.__str__()

    def is_complete(self):
        return len(gramatica[self.rule_index].right) == self.prox

    def __iter__(self):
        return iter((self.rule_index, self.prox, self.start))


def next_symbol(grammar: Grammar, state: State):
    rule = grammar[state.rule_index]
    length = len(rule.right)
    return rule.right[state.prox] if not state.prox == length else None


def predict(states: list[IndexedSet[State]], i: int, symbol: str, grammar: Grammar):
    for rule_index, rule in enumerate(grammar):
        if rule.left == symbol:
            states[i].add(State(rule_index, 0, i))
    return states


def scan(states: list[IndexedSet[State]], i: int, j: int, symbol: Terminal, input_str):
    item = states[i][j]
    if symbol(input_str[i : i + 1]):
        if len(states[i + 1 : i + 2]) == 0:  # if next state's list is empty
            states.append(IndexedSet())
        states[i + 1].add(State(item.rule_index, item.prox + 1, item.start))
    return states


def complete(states: list[IndexedSet[State]], i: int, j: int, grammar: Grammar):
    item = states[i][j]
    for old_item in states[item.start]:
        if next_symbol(grammar, old_item) == grammar[item.rule_index].left:
            states[i].add(State(old_item.rule_index, old_item.prox + 1, old_item.start))
    return states


def build_items(
    grammar: Grammar, input_str: str, starting_item: str
) -> list[IndexedSet[State]]:
    """
    Build and iterate through states for given grammar
    and `input_str`.
    """
    states: list[IndexedSet[State]] = [
        IndexedSet(
            [State(i, 0, 0) for i, r in enumerate(grammar) if r.left == starting_item]
        )
    ]
    i = 0
    while i < len(states):
        j = 0
        while j < len(states[i]):
            state = states[i][j]
            next_sym = next_symbol(grammar, state)
            if next_sym is None:
                states = complete(states, i, j, grammar)
            elif callable(next_sym):
                states = scan(states, i, j, next_sym, input_str)
            elif type(next_sym) is str:
                states = predict(states, i, next_sym, grammar)
            else:
                raise Exception("Regra inválida")
            j += 1
        i += 1
    return states


def invert_items(
    states: list[IndexedSet[State]], grammar: Grammar
) -> list[list[State]]:
    flat_states = [
        (original_index, s) for original_index, l in enumerate(states) for s in l
    ]
    return [
        [
            State(s.rule_index, s.prox, original_index)
            for original_index, s in flat_states
            if s.start == i
        ]
        for i in range(len(states))
    ]


def parse_items(
    states: list[IndexedSet[State]], string: str, grammar: Grammar, starting_item: str
) -> Union[list[dict], None]:
    """
    Reads a list of states and parses it into a dict that represents its structure.
    """
    completed_states = [[s for s in l if s.is_complete()] for l in states]
    inverted_states = invert_items(completed_states, grammar)

    initial_elements = [
        s
        for s in inverted_states[0]
        if grammar[s.rule_index].left == starting_item
        and s.start == len(inverted_states) - 1
    ]
    return [
        recursive_build(states, grammar, string, 0, (rule, finish))
        for rule, _, finish in initial_elements
    ]


def recursive_build(
    states: list[IndexedSet[State]],
    grammar: Grammar,
    string: str,
    initial_state: int,
    edge: tuple[int, int],
) -> dict:
    """
    Recursively build items from states.

    TODO: this.
    """
    rule_index, finish = edge


if __name__ == "__main__":

    setrecursionlimit(50)

    gramatica = [
        Rule("Sum", ["Sum", chars("+-"), "Product"]),
        Rule("Sum", ["Product"]),
        Rule("Product", ["Product", chars("*/"), "Factor"]),
        Rule("Product", ["Factor"]),
        Rule("Factor", [chars("("), "Sum", chars(")")]),
        Rule("Factor", ["Number"]),
        Rule("Number", [range_number("09"), "Number"]),
        Rule("Number", [range_number("09")]),
    ]

    from pprint import pprint
    from json import dumps

    string = "1+(2*3-4)"
    states = build_items(gramatica, string, "Sum")
    parse_dict = parse_items(states, string, gramatica, "Sum")
