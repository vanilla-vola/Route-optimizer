class MatrixError(Exception):
    """Raised when distance/duration matrix construction fails."""


class OptimizationError(Exception):
    """Raised when the TSP solver cannot find a feasible route."""
