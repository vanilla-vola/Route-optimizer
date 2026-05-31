from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.core.exceptions import OptimizationError

FirstSolutionStrategy = routing_enums_pb2.FirstSolutionStrategy


def solve_route(
    duration_matrix: list[list[int]],
    *,
    start_fixed: bool,
    end_fixed: bool,
    round_trip: bool,
    time_limit_s: int = 5,
    first_solution_strategy: int = FirstSolutionStrategy.PATH_CHEAPEST_ARC,
) -> tuple[list[int], int]:
    n = len(duration_matrix)
    if n == 0:
        return [], 0
    if n == 1:
        return [0], 0

    if round_trip:
        return _solve_round_trip(
            duration_matrix,
            time_limit_s=time_limit_s,
            first_solution_strategy=first_solution_strategy,
        )

    start_node, end_node = _open_path_terminals(
        n,
        start_fixed=start_fixed,
        end_fixed=end_fixed,
    )
    return _solve_open_path(
        duration_matrix,
        start_node=start_node,
        end_node=end_node,
        time_limit_s=time_limit_s,
        first_solution_strategy=first_solution_strategy,
    )


def solve_segment(
    duration_matrix: list[list[int]],
    nodes: list[int],
    *,
    round_trip: bool,
    start_fixed: bool,
    end_fixed: bool,
    time_limit_s: int = 2,
    first_solution_strategy: int = FirstSolutionStrategy.PATH_CHEAPEST_ARC,
) -> list[int]:
    """Re-order `nodes` while preserving first/last when fixed on an open path."""
    if len(nodes) <= 2:
        return list(nodes)

    sub: list[list[int]] = [
        [duration_matrix[nodes[i]][nodes[j]] for j in range(len(nodes))]
        for i in range(len(nodes))
    ]

    if round_trip:
        order_local, _ = _solve_round_trip(
            sub,
            time_limit_s=time_limit_s,
            first_solution_strategy=first_solution_strategy,
        )
    else:
        local_start = 0 if start_fixed else 0
        local_end = len(nodes) - 1 if end_fixed else len(nodes)
        order_local, _ = _solve_open_path(
            sub,
            start_node=local_start,
            end_node=local_end,
            time_limit_s=time_limit_s,
            first_solution_strategy=first_solution_strategy,
        )

    return [nodes[i] for i in order_local]


def _solve_round_trip(
    duration_matrix: list[list[int]],
    *,
    time_limit_s: int,
    first_solution_strategy: int,
) -> tuple[list[int], int]:
    n = len(duration_matrix)
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index: int, to_index: int) -> int:
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return duration_matrix[i][j]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    solution = routing.SolveWithParameters(
        _search_params(time_limit_s, first_solution_strategy)
    )
    if solution is None:
        raise OptimizationError(
            "No feasible route found. Some stops may be unreachable — try repositioning them."
        )

    index = routing.Start(0)
    order: list[int] = []
    total = 0

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        order.append(node)
        next_index = solution.Value(routing.NextVar(index))
        total += routing.GetArcCostForVehicle(index, next_index, 0)
        index = next_index

    order.append(manager.IndexToNode(index))

    if len(order) > 1 and order[0] == order[-1]:
        order = order[:-1]

    return order, int(total)


def _solve_open_path(
    duration_matrix: list[list[int]],
    *,
    start_node: int,
    end_node: int,
    time_limit_s: int,
    first_solution_strategy: int,
) -> tuple[list[int], int]:
    """Open path TSP using a zero-cost dummy end node when the end is flexible."""
    n = len(duration_matrix)
    dummy_end = n
    size = n + 1

    extended = [[0] * size for _ in range(size)]
    for i in range(n):
        for j in range(n):
            extended[i][j] = duration_matrix[i][j]
        extended[i][dummy_end] = 0

    manager = pywrapcp.RoutingIndexManager(size, 1, [start_node], [dummy_end])
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index: int, to_index: int) -> int:
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return extended[i][j]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    solution = routing.SolveWithParameters(
        _search_params(time_limit_s, first_solution_strategy)
    )
    if solution is None:
        raise OptimizationError(
            "No feasible route found. Some stops may be unreachable — try repositioning them."
        )

    index = routing.Start(0)
    order: list[int] = []
    total = 0

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node < n:
            order.append(node)
        next_index = solution.Value(routing.NextVar(index))
        total += routing.GetArcCostForVehicle(index, next_index, 0)
        index = next_index

    if end_node < n and (not order or order[-1] != end_node):
        order.append(end_node)

    return order, int(total)


def _open_path_terminals(
    n: int,
    *,
    start_fixed: bool,
    end_fixed: bool,
) -> tuple[int, int]:
    start_node = 0 if start_fixed else 0
    if end_fixed:
        return start_node, n - 1
    return start_node, n  # flexible end via dummy node


def _search_params(time_limit_s: int, first_solution_strategy: int):
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = first_solution_strategy
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.FromSeconds(max(1, time_limit_s))
    return search_params
