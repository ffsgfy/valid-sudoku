#include <vector>
#include <limits>
#include <unordered_map>
#include <unordered_set>
#include <random>
#include <utility>
#include <algorithm>
#include <functional>
#include <bit>

constexpr int ORDER = 3;
constexpr int SIZE_1 = (ORDER * ORDER);
constexpr int SIZE_2 = (SIZE_1 * SIZE_1);

constexpr int ROW = 0;
constexpr int COL = 1;
constexpr int BLK = 2;

constexpr int MASK_FULL = ((1 << SIZE_1) - 1);
constexpr int SCORE_STEP = SIZE_2;

inline int bit_length(int x) {
    x |= x >> 1;
    x |= x >> 2;
    x |= x >> 4;
    x |= x >> 8;
    x |= x >> 16;
    return std::popcount((unsigned int)x);
    // return std::bit_width((unsigned int)x);
}

inline int bit_count(int x) {
    return std::popcount((unsigned int)x);
}

inline int mask_encode(int value) {
    return 1 << value;
}

inline int mask_decode(int mask) {
    return bit_length(mask & (-mask)) - 1;
}

// Returns the index of a cell given as an offset into one of its groups
inline int group_combine(int group, int index, int offset) {
    switch (group) {
        // index = row, offset = col
        case ROW: return index * SIZE_1 + offset;
        // index = col, offset = row
        case COL: return offset * SIZE_1 + index;
        // index = blk_outer, offset = blk_inner (see Grid.update())
        case BLK: return \
            ((index / ORDER) * ORDER + offset / ORDER) * SIZE_1 + \
            ((index % ORDER) * ORDER + offset % ORDER);
    }

    return 0;
}

class Solver {
public:
    // Callback invoked when a solution has been found; returning `true` stops the search
    using callback_t = std::function<bool(const std::vector<int>& cells, int score)>;
    using result_t = std::pair<std::vector<int>, int>; // (cells, score)

    Solver() {
        m_indexes.resize(SIZE_2, 0);
        for (int i = 0; i < SIZE_2; ++i) {
            m_indexes[i] = i;
        }

        m_cells.resize(SIZE_2, MASK_FULL);
        m_groups.resize(SIZE_2 * 3, MASK_FULL);
        m_rng.seed(std::random_device{}());
    }

private:
    // Method implementing constraint propagation.
    // Updates the bitmask of a cell given by its index and fully propagates the effects to other cells.
    // Returns `false` if the grid's state became invalid in the process, `true` otherwise
    bool update(int index, int mask) {
        std::unordered_map<int, int> updates{{index, mask}};

        // Each update clears some bits of a cell's mask (by way of a bitwise and),
        // which are then used to update group masks and potentially enqueue updates to other cells
        while (updates.size() > 0) {
            index = updates.begin()->first;
            mask = updates.begin()->second;
            updates.erase(updates.begin());

            int mask_old = m_cells[index];
            int mask_new = mask_old & mask;
            int delta = mask_old & ~mask; // bits cleared by this update

            if (mask_new == 0) {
                return false;
            }
            else if (delta == 0) {
                continue;
            }
            else {
                m_cells[index] = mask_new;
            }

            int row = index / SIZE_1;
            int col = index % SIZE_1;
            int blk_outer = (row / ORDER) * ORDER + (col / ORDER) % ORDER; // index of this cell's block
            int blk_inner = (row % ORDER) * ORDER + col % ORDER; // index of this cell inside its block

            // Indexes of the groups that this cell belongs to
            int group_indexes[] = {row, col, blk_outer};

            // Offsets to the beginning of each of this cell's groups in m_groups
            int group_bases[] = {
                ROW * SIZE_2 + row * SIZE_1,
                COL * SIZE_2 + col * SIZE_1,
                BLK * SIZE_2 + blk_outer * SIZE_1,
            };

            // Masked positions of this cell inside its groups
            int group_bits[] = {mask_encode(col), mask_encode(row), mask_encode(blk_inner)};

            // Iterate over the just-cleared bits
            for (int delta_value = 0; delta_value < SIZE_1; ++delta_value) {
                int delta_bit = mask_encode(delta_value);
                if ((delta_bit & delta) == 0) {
                    continue;
                }

                // This cell can no longer be set to delta_value, which needs to be reflected in our group masks
                for (int group = 0; group < 3; ++group) {
                    int group_base = group_bases[group];
                    int group_mask = m_groups[group_base + delta_value] & ~group_bits[group];

                    // Fail if delta_value has no viable positions left inside this group
                    if (group_mask == 0) {
                        return false;
                    }
                    else {
                        m_groups[group_base + delta_value] = group_mask;
                    }

                    // If delta_value has only one viable position, place it there via an update
                    if (bit_count(group_mask) == 1) {
                        // Find the index of the target cell
                        int target = group_combine(group, group_indexes[group], mask_decode(group_mask));
                        int target_mask = updates[target];
                        if (target_mask == 0) {
                            target_mask = MASK_FULL;
                        }

                        // Fail if delta_value cannot be placed in the target cell
                        if ((target_mask &= m_cells[target] & delta_bit) == 0) {
                            return false;
                        }
                        else {
                            updates[target] = target_mask;
                        }
                    }
                }
            }

            // If the updated cell has only one possible value left, make sure this value
            // does not appear anywhere else inside any of the cell's groups
            if (bit_count(mask_new) == 1) {
                int value = mask_decode(mask_new);
                int group_masks[] = {
                    m_groups[group_bases[ROW] + value],
                    m_groups[group_bases[COL] + value],
                    m_groups[group_bases[BLK] + value],
                };

                // Group masks for the value are used to locate cells that need to be updated
                // (this is more efficient than iterating through all potentially affected cells)
                for (int group = 0; group < 3; ++group) {
                    int group_index = group_indexes[group];
                    int group_mask = group_masks[group];
                    int group_bit = group_bits[group]; // bit to be skipped (corresponding to the updated cell)

                    // Iterate over set bits in the group mask
                    for (int offset = 0; offset < SIZE_1; ++offset) {
                        int offset_bit = mask_encode(offset);
                        if ((offset_bit == group_bit) || ((offset_bit & group_mask) == 0)) {
                            continue;
                        }

                        // Find the index of the cell from which to remove our value
                        int target = group_combine(group, group_index, offset);
                        int target_mask = updates[target];
                        if (target_mask == 0) {
                            target_mask = MASK_FULL;
                        }

                        // Fail if the target cell has no other possible values left
                        if ((target_mask &= m_cells[target] & ~mask_new) == 0) {
                            return false;
                        }
                        else {
                            updates[target] = target_mask;
                        }
                    }
                }
            }
        }

        return true;
    }

    // Method implementing recursive tree search.
    // Calls the `callback` when a solution is found, stopping the search if it returns `true`;
    // the method's return value indicates whether this occurred or not
    bool solve_step(bool randomize, const callback_t& callback, int score) {
        int best_index = 0;
        int best_mask = 0;
        int best_count = -1;

        // From yet unfilled cells choose the one with the lowest number of possible values
        // In this implementation there seems to always be exactly one cell with exactly two possible values
        // (provided that the initial state was uniquely solvable and all bitmasks were properly update()ed),
        // which means that checking bitcounts in m_groups the same way as in m_cells would be redundant
        for (int i = 0; i < SIZE_2; ++i) {
            int index = randomize ? m_indexes[i] : i;
            int mask = m_cells[index];
            int count = bit_count(mask);

            // Zero masks are caught by update(), no need to check for them
            if (count == 1) {
                continue;
            }

            if ((count < best_count) || (best_count < 0)) {
                best_index = index;
                best_mask = mask;
                best_count = count;

                // 2 is the smallest possible bitcount here
                if (count == 2) {
                    break;
                }
            }
        }

        if (best_count < 0) {
            // All cells are filled, we are done
            return callback(m_cells, score); 
        }
        else if (best_count > 1) {
            std::vector<int> bits;

            // Extract individual set bits from best_mask
            for (int value = 0; value < SIZE_1; ++value) {
                int bit = mask_encode(value);
                if ((bit & best_mask) != 0) {
                    bits.push_back(bit);
                }
            }

            if (randomize) {
                std::shuffle(bits.begin(), bits.end(), m_rng);
            }

            m_guesses.push_back(best_index);

            // Try to place every extracted bit/value in the chosen cell
            for (int bit : bits) {
                std::vector<int> backup_cells = m_cells;
                std::vector<int> backup_groups = m_groups;

                if (update(best_index, bit)) {
                    if (solve_step(randomize, callback, score + SCORE_STEP)) {
                        return true; // NOTE: m_guesses is intentionally not restored
                    }
                }

                m_cells = std::move(backup_cells);
                m_groups = std::move(backup_groups);
            }

            m_guesses.pop_back();
        }

        return false;
    }

public:
    bool solve(const std::vector<int>& initial, bool randomize, const callback_t& callback) {
        if (initial.size() != SIZE_2) {
            return false;
        }

        bool result = true;
        int score = 0;

        // Find all non-full cell masks and update() on them
        for (int index = 0; index < SIZE_2; ++index) {
            int mask = initial[index];

            // Initially, score = number of unfilled cells
            // Later it is incremented by SCORE_STEP on every recursive solve_step() call
            if (bit_count(mask) > 1) {
                score += 1;
            }

            if (mask != MASK_FULL) {
                if (!(result = update(index, mask))) {
                    break;
                }
            }
        }

        if (result) {
            m_guesses.clear();

            if (randomize) {
                std::shuffle(m_indexes.begin(), m_indexes.end(), m_rng);
            }

            result = solve_step(randomize, callback, score);
        }

        // Restore the bitmasks
        std::fill(m_cells.begin(), m_cells.end(), MASK_FULL);
        std::fill(m_groups.begin(), m_groups.end(), MASK_FULL);

        return result;
    }

    std::vector<result_t> solve(const std::vector<int>& initial, bool randomize, int limit) {
        std::vector<result_t> results;

        if (limit > 0) {
            auto callback = [&](const std::vector<int>& cells, int score) -> bool {
                results.push_back({cells, score});
                return results.size() >= (size_t)limit;
            };

            solve(initial, randomize, callback);
        }

        return results;
    }

    result_t generate_once() {
        // Solve an empty grid with randomization
        auto [solution, score] = solve(m_cells, true, 1)[0];
        std::vector<int> guesses = m_guesses;
        std::vector<int> result = m_cells;

        // Fill in all the guessed values in the resulting state
        // This way it is guaranteed to have a unique solution
        for (int index : guesses) {
            result[index] = solution[index];
        }

        // Randomize further
        std::shuffle(guesses.begin(), guesses.end(), m_rng);

        // Set up a callback for solve() that counts (up to two) solutions and saves their scores
        int score_tmp = score;
        int counter = 0;
        auto callback = [&](const std::vector<int>&, int s) -> bool {
            score_tmp = s;
            return (++counter) > 1;
        };

        // Try to remove the guessed values one by one while preserving the uniqueness of our solution
        for (int index : guesses) {
            result[index] = MASK_FULL;
            counter = 0;

            // Put the value back if our solution ceases to be unique
            if (solve(result, false, callback)) {
                result[index] = solution[index];
            }
            else {
                score = score_tmp;
            }
        }

        // The resulting state is minimal
        return {result, score};
    }

    result_t generate(int score_min, int score_max, int limit) {
        if (score_min < 0) {
            score_min = 0;
        }

        if (score_max < 0) {
            score_max = std::numeric_limits<int>::max();
        }

        int score_target = score_min / 2 + score_max / 2;

        std::vector<int> best_result;
        int best_score = -1;
        int best_distance = -1;

        // Loop is executed at least once
        do {
            auto [result, score] = generate_once();
            int distance = std::abs(score - score_target);

            if ((distance < best_distance) || (best_distance < 0)) {
                best_result = std::move(result);
                best_score = score;
                best_distance = distance;

                if ((score_min <= score) && (score <= score_max)) {
                    break;
                }
            }
        }
        while (--limit > 0);

        return {best_result, best_score};
    }

private:
    std::vector<int> m_cells; // bitmasks of possible values for every cell
    std::vector<int> m_groups; // bitmasks of possible positions for each value in each group
    std::vector<int> m_guesses; // stack of indexes of cells whose values were guessed in solve_step()
    std::vector<int> m_indexes; // list of indexes for randomizing cell iteration order
    std::mt19937 m_rng;
};

// Returns the indexes of all cells which are in conflict with any other cell
std::unordered_set<int> list_conflicts(const std::vector<int>& state) {
    std::unordered_set<int> result;
    std::vector<int> groups; // stores the index of each value in every group (or -1 by default)

    if (state.size() == SIZE_2) {
        groups.resize(SIZE_2 * 3, -1);

        // Iterate over filled cells
        for (int index = 0; index < SIZE_2; ++index) {
            int mask = state[index];
            if (bit_count(mask) != 1) {
                continue;
            }

            int value = mask_decode(mask);
            int row = index / SIZE_1;
            int col = index % SIZE_1;
            int blk = (row / ORDER) * ORDER + (col / ORDER) % ORDER;
            int group_indexes[] = {row, col, blk};

            // Store the index of this value in each of this cell's groups
            // If one of these indexes is already set - there is a conflict
            for (int group = 0; group < 3; ++group) {
                int offset = group * SIZE_2 + group_indexes[group] * SIZE_1 + value;
                if (groups[offset] < 0) {
                    groups[offset] = index;
                }
                else {
                    result.insert(groups[offset]);
                    result.insert(index);
                }
            }
        }
    }

    return result;
}

// Returns a mask of possible values for the given cell index
int list_candidates(const std::vector<int>& state, int index) {
    int mask = MASK_FULL;
    int row = index / SIZE_1;
    int col = index % SIZE_1;
    int blk = (row / ORDER) * ORDER + (col / ORDER) % ORDER;
    int group_indexes[] = {row, col, blk};

    for (int group = 0; group < 3; ++group) {
        for (int offset = 0; offset < SIZE_1; ++offset) {
            int other_index = group_combine(group, group_indexes[group], offset);
            int other_mask = state[other_index];
            if ((other_index != index) && (bit_count(other_mask) == 1)) {
                mask &= ~other_mask;
            }
        }
    }

    return mask;
}

