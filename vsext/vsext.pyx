# distutils: language = c++
# distutils: extra_compile_args = -std=c++20

from libcpp.vector cimport vector
from libcpp.utility cimport pair
from libcpp.unordered_set cimport unordered_set


cdef extern from "vsext_impl.cpp":
    const int SIZE_1
    const int SIZE_2
    const int MASK_FULL
    const int SCORE_STEP

    cdef cppclass SolverImpl "Solver":
        SolverImpl() except +
        vector[pair[vector[int], int]] solve(const vector[int]& initial, bint randomize, int limit) except +
        pair[vector[int], int] generate_once() except +
        pair[vector[int], int] generate(int score_min, int score_max, int limit) except +

    inline int bit_length_impl "bit_length"(int x);
    inline int bit_count_impl "bit_count"(int x);

    unordered_set[int] list_conflicts_impl "list_conflicts"(const vector[int]& state) except +
    int list_candidates_impl "list_candidates"(const vector[int]& state, int index) except +


score_step = SCORE_STEP


cdef class Solver:
    cdef SolverImpl solver

    def solve(self, initial: list[int], randomize: bool = False, limit: int = 2) -> list[tuple[list[int], int]]:
        return self.solver.solve(initial, randomize, limit)

    def generate_once(self) -> tuple[list[int], int]:
        return self.solver.generate_once()

    def generate(self, score_min: int, score_max: int, limit: int) -> tuple[list[int], int]:
        return self.solver.generate(score_min, score_max, limit)


def list_conflicts(state: list[int]) -> set[int]:
    return list_conflicts_impl(state)


def list_candidates(state: list[int], index: int) -> int:
    return list_candidates_impl(state, index)


def bit_length(x: int) -> int:
    return bit_length_impl(x)


def bit_count(x: int) -> int:
    return bit_count_impl(x)


def encode_mask(value: int) -> int:
    return (1 << value) if value >= 0 else MASK_FULL


def decode_mask(mask: int) -> int:
    if bit_count_impl(mask) != 1:
        return -1

    return bit_length_impl(mask & (-mask)) - 1


def encode_state(state: list[int]) -> str:
    if (len(state) != SIZE_2) or any(x < 0 or x > MASK_FULL for x in state):
        return ""

    return "".join(map(lambda x: str(decode_mask(x) + 1), state)).replace("0", ".")


def decode_state(state: str) -> list[int] | None:
    state = state.replace(".", "0")

    if (len(state) != SIZE_2) or not state.isdecimal():
        return None

    return list(map(lambda x: encode_mask(int(x) - 1), state))

