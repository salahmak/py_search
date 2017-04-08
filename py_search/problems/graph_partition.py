from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from random import random
from random import shuffle
from random import choice

from py_search.base import Problem
from py_search.base import Node
from py_search.utils import compare_searches
from py_search.optimization import hill_climbing
from py_search.optimization import simulated_annealing
from py_search.optimization import branch_and_bound


def generate_graph(n, p):
    """
    Generates a random graph for graph partitioning. n specifies the number of
    nodes and p specifies the probability that any pair of nodes has a
    transition.
    """
    V = set([i for i in range(n)])
    E = []
    for n1 in range(n):
        for n2 in range(n1+1, n):
            if random() < p:
                E.append((n1, n2))

    return V, E


def random_partition(V):
    V = list(V)
    shuffle(V)
    return frozenset(V[:len(V)//2])


class LocalGraphPartitionProblem(Problem):
    """
    This class represents a local search version of the graph partition
    problem.  I.e., a random state is generated to start the search and then
    neighbors of the state can be expanded in order to reduce the solution
    cost.
    """
    def node_value(self, node):
        """
        This function is used by the branch_and_bound approach to determine
        whether successor nodes have the potential to be better than the
        current node. If this just returns the node cost, then the algorithm
        will explore nodes greedily.
        """
        return node.cost()

    def random_successor(self, node):
        """
        A function that returns a random successor of the current node. This is
        used by the simulated annealing function, so it doesn't have to expand
        all successors.

        A successor is generated by randomly flipping a pair of row to column
        assignments.
        """
        p = set(node.state)
        V, E = node.extra
        not_p = V - p

        pV = choice(list(p))
        not_pV = choice(list(not_p))

        p.remove(pV)
        p.add(not_pV)

        return Node(frozenset(p), node, node_cost=cutsize(E, p),
                    extra=node.extra)

    def successors(self, node):
        """
        Generates successor states by flipping each pair of row to column
        assignments.
        """
        p = node.state
        V, E = node.extra
        not_p = V - p

        for pV in p:
            for not_pV in not_p:
                new_p = set(p)
                new_p.remove(pV)
                new_p.add(not_pV)

                yield Node(frozenset(new_p), node, node_cost=cutsize(E, p),
                           extra=node.extra)

    def random_node(self):
        """
        Generates a node that has a random assignment.
        """
        V, E = self.initial.extra
        p = random_partition(V)
        return Node(p, node_cost=cutsize(E, p),
                    extra=self.initial.extra)

    def goal_test(self, node):
        """
        The search should never terminate early.
        """
        return False


def cutsize(E, p):
    cuts = [e for e in E if (e[0] in p and e[1] not in p) or
                            (e[0] not in p and e[1] in p)]
    return len(cuts)


if __name__ == "__main__":

    n = 30
    p = 20 / (n-1)
    print(n, p)
    V, E = generate_graph(n, p)
    initial = random_partition(V)
    cost = cutsize(E, initial)

    print("######################################")
    print("Local Search / Optimization Techniques")
    print("######################################")

    problem = LocalGraphPartitionProblem(initial, initial_cost=cost,
                                         extra=(V, E))

    print("Initial Assignment Cost:")
    print(cutsize(E, initial))
    print("Number of successors:")
    print(len(list(problem.successors(problem.initial))))
    print()

    def annealing(problem):
        size = (n * (n//2)) // 2
        return simulated_annealing(problem, initial_temp=5.5, temp_length=size)

    def greedy_annealing(problem):
        size = (n * (n//2)) // 2
        return simulated_annealing(problem, initial_temp=0, temp_length=size)

    def depth_limited_branch_and_bound(problem):
        return branch_and_bound(problem, depth_limit=100)

    compare_searches(problems=[problem],
                     searches=[hill_climbing, annealing, greedy_annealing,
                               branch_and_bound])
