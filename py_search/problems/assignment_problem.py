from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from itertools import combinations
from random import normalvariate
from random import shuffle
from random import randint

from munkres import Munkres

from py_search.base import Problem
from py_search.base import Node
from py_search.utils import compare_searches
from py_search.informed import best_first_search
from py_search.informed import beam_search
from py_search.optimization import branch_and_bound
from py_search.optimization import hill_climbing
from py_search.optimization import simulated_annealing
from py_search.optimization import local_beam_search


def random_matrix(n):
    """
    Generates an a list of list of floats (representing an n x n matrix) where
    the values have mean 0 and std 1.

    This is used as cost matrix for an assignment problem.
    """
    return [[normalvariate(0, 1) for j in range(n)] for i in range(n)]


class AssignmentProblem(Problem):
    """
    A tree search version of the assignment problem. Starts with an initially
    empty assignment and then incrementally builds the assignment up adding one
    assignment per expansion.
    """

    def min_cost_heuristic(self, node):
        """
        A huristic specifying the minimum cost that could be achieved for
        unassigned rows.
        """
        node.state
        costs, unassigned = node.extra

        empty_rows = [i for i, v in enumerate(node.state) if v is None]

        min_possible = 0
        for r in empty_rows:
            sub_c = [v for i, v in enumerate(costs[r]) if i in unassigned]
            min_possible += min(sub_c)

        return min_possible

    def node_value(self, node):
        """
        The value of a node is the combination of the node cost and the
        min_cost heuristic
        """
        return node.cost() + self.min_cost_heuristic(node)

    def successors(self, node):
        """
        An iterator that yields the sucessors of the provided node.
        """
        state = node.state
        costs, unassigned = node.extra

        for i, v in enumerate(state):
            if v is None:
                for u in unassigned:
                    new_state = tuple([u if i == j else k
                                       for j, k in enumerate(state)])
                    new_unassigned = tuple([k for k in unassigned if k != u])

                    c = node.cost() + costs[i][u]
                    yield Node(new_state, node, (i, u), c,
                               extra=(costs, new_unassigned))

    def goal_test(self, node):
        """
        A test of whether a complete assignment has been reached.
        """
        state = node.state
        return None not in state


class LocalAssignmentProblem(Problem):
    """
    This class represents a local search version of the assignment problem.
    I.e., a random state is generated to start the search and then neighbors of
    the state can be expanded in order to reduce the solution cost.
    """

    def node_value(self, node):
        """
        Returns a lower bound on the solution cost reachable from the given
        node (or its children)
        """
        return float('-inf')

    def random_successor(self, node):
        """
        A function that returns a random successor of the current node. This is
        used by the simulated annealing function, so it doesn't have to expand
        all successors.

        A successor is generated by randomly flipping a pair of row to column
        assignments.
        """
        costs = node.extra[0]

        p = [0, 0]
        p[0] = randint(0, len(node.state)-1)
        p[1] = p[0]
        while p[0] == p[1]:
            p[1] = randint(0, len(node.state)-1)

        new_cost = node.cost()
        new_cost -= costs[p[0]][node.state[p[0]]]
        new_cost -= costs[p[1]][node.state[p[1]]]
        new_cost += costs[p[0]][node.state[p[1]]]
        new_cost += costs[p[1]][node.state[p[0]]]

        state = list(node.state)
        temp = state[p[0]]
        state[p[0]] = state[p[1]]
        state[p[1]] = temp

        return Node(tuple(state), node, p, new_cost, extra=node.extra)

    def successors(self, node):
        """
        Generates successor states by flipping each pair of row to column
        assignments.
        """
        costs = node.extra[0]

        for p in combinations(node.state, 2):
            new_cost = node.cost()
            new_cost -= costs[p[0]][node.state[p[0]]]
            new_cost -= costs[p[1]][node.state[p[1]]]
            new_cost += costs[p[0]][node.state[p[1]]]
            new_cost += costs[p[1]][node.state[p[0]]]

            state = list(node.state)
            temp = state[p[0]]
            state[p[0]] = state[p[1]]
            state[p[1]] = temp

            yield Node(tuple(state), node, p, new_cost, extra=node.extra)

    def random_node(self):
        """
        Generates a node that has a random assignment.
        """
        state = random_assignment(len(self.initial.state))
        return Node(state, node_cost=cost(state, self.initial.extra[0]),
                    extra=self.initial.extra)

    def goal_test(self, node):
        return False


def random_assignment(n):
    """
    Returns a random valid assignment for an n x n matrix
    """
    state = list(range(n))
    shuffle(state)
    return tuple(state)


def cost(assignment, costs):
    """
    Given an assignemnt and a cost matrix, returns the cost of the
    assignment.
    """
    cost = 0.0
    for row, col in enumerate(assignment):
        cost += costs[row][col]
    return cost


def print_matrix(m):
    """
    Print a matrix
    """
    for row in m:
        print("\t".join(["%0.2f" % v for v in row]))


if __name__ == "__main__":

    n = 8
    costs = random_matrix(n)

    print()
    print("####################################################")
    print("Randomly generated square cost matrix (%i x %i)" % (n, n))
    print("####################################################")
    print_matrix(costs)

    print()
    print("####################################################")
    print("Optimial solution using Munkres/Hungarian Algorithm")
    print("####################################################")

    m = Munkres()
    indices = m.compute(costs)
    best = tuple([v[1] for v in indices])
    print("Munkres Solution:")
    print(best)
    print("Munkres Cost:")
    print(cost(best, costs))
    print()

    print("######################################")
    print("Local Search / Optimization Techniques")
    print("######################################")

    initial = random_assignment(n)
    problem = LocalAssignmentProblem(initial,
                                     initial_cost=cost(initial, costs),
                                     extra=(costs,))
    print("Initial Assignment (randomly generated):")
    print(initial)
    print("Initial Assignment Cost:")
    print(problem.initial.cost())
    print()

    def local_beam_width2(problem):
        return local_beam_search(problem, beam_width=2)

    def greedy_annealing(problem):
        num_neighbors = (n * (n-1)) // 2
        return simulated_annealing(problem, initial_temp=0,
                                   temp_length=num_neighbors)

    def annealing(problem):
        num_neighbors = (n * (n-1)) // 2
        return simulated_annealing(problem, initial_temp=1.5,
                                   temp_length=num_neighbors)

    def depth_limited_branch_and_bound(problem):
        return branch_and_bound(problem, depth_limit=4)

    compare_searches(problems=[problem],
                     searches=[depth_limited_branch_and_bound,
                               hill_climbing,
                               local_beam_width2,
                               greedy_annealing,
                               annealing])

    print()
    print("###########################")
    print("Informed Search Techniques")
    print("###########################")

    # TREE SEARCH APPROACH
    empty = tuple([None for i in range(len(costs))])
    unassigned = [i for i in range(len(costs))]

    new_costs = [[c - min(row) for c in row] for row in costs]
    min_c = [min([row[c] for row in costs]) for c, v in enumerate(costs[0])]
    new_costs = [[v - min_c[c] for c, v in enumerate(row)] for row in costs]

    tree_problem = AssignmentProblem(empty, extra=(costs, unassigned))

    def beam_width2(problem):
        return beam_search(problem, beam_width=2)

    print()
    compare_searches(problems=[tree_problem],
                     searches=[beam_width2,
                               best_first_search])
