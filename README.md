# Curve Math Equivalence Tests

This project tests the mathematical equivalence between Vyper StableswapMath contract and the C++ cryptopool-simulator. It verifies that the `Newton_D` and `get_y` mathematical functions produce identical results, proving that the A parameter can be deployed with confidence.

## Structure

```
.
├── cryptopool-simulator/    # Git submodule (extra_boost branch)
├── twocrypto-ng/           # Git submodule (invariant-change branch)
├── pyproject.toml          # Project dependencies
├── src/
│   ├── cpp_wrapper.cpp     # C++ wrapper that adjusts A parameter
│   └── test_equivalence.py # Main test script
└── README.md
```

## Prerequisites

- Python 3.12+
- g++ compiler
- git

## Setup

1. Clone the repository with submodules:
```bash
git clone --recurse-submodules <repository-url>
cd <repository-name>
```

Or if you already cloned without submodules:
```bash
git submodule update --init --recursive
```

2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

3. Install Python dependencies:
```bash
uv sync
```

## Running Tests

Run the equivalence tests:
```bash
uv run python src/test_equivalence.py
```

The test script will:
1. Compile the C++ wrapper dynamically using g++
2. Deploy the Vyper StableswapMath contract using titanoboa
3. Run comprehensive equivalence tests comparing Newton_D and get_y
4. Clean up generated files (.so library)

## Test Output

You should see output like:
```
================================================================================
Curve Math Equivalence Tests
================================================================================
Compiling C++ library...
✓ C++ library compiled
Deploying Vyper contract...
✓ Vyper contract deployed

=== Newton_D Tests ===
Description          Vyper D                        C++ D                          Rel Error      
-----------------------------------------------------------------------------------------------
Equal balances       2000000000000000000000000      1999999999999999966445568      1.68e-17        ✓
3:1 ratio            1991966318386556376403531      1991966318386556446965760      3.54e-17        ✓
...

✅ All tests passed! Math implementations are equivalent.
The A parameter can be deployed with confidence.
```

## Key Finding: A Parameter Scaling

The C++ simulator expects raw A values, while the Vyper contract internally divides A by A_MULTIPLIER (10000). To ensure equivalence:

- **Vyper contract**: Pass A pre-multiplied by 10000 (e.g., A=100 → pass 1000000)
- **C++ simulator**: Pass raw A values (e.g., A=100 → pass 100)

The test script (`src/test_equivalence.py`) handles this by dividing the Vyper A value by 10000 when calling C++ functions:
```python
# Vyper call with pre-multiplied A
vyper_D = stableswap.newton_D_2(A, gamma, [x0, x1], D0)

# C++ call with raw A (divide by 10000)
cpp_D = cpp_lib.python_newton_D_2(A / 10000, gamma, x0, x1, D0)
```

## Test Cases

The tests cover:
- Equal balance pools (1:1 ratio)
- Imbalanced pools (3:1, 5:3, 11:9, 19:1 ratios)
- Various A parameter values (100k to 1.6M)
- Edge cases (small amounts, large imbalances)

## Results

All tests pass with relative errors < 1e-15, which is within expected floating-point precision limits. This confirms that:
1. The mathematical implementations are equivalent
2. The A parameter can be safely deployed
3. The simulator accurately represents the on-chain behavior

## Updating Submodules

To pull the latest changes from the submodule repositories:
```bash
git submodule update --remote --merge
```

## Development

To run tests with manual compilation:
```bash
# Compile C++ wrapper
g++ -shared -fPIC -o cpp_math.so src/cpp_wrapper.cpp -O3 -std=c++17 -I./cryptopool-simulator

# Run tests
uv run python src/test_equivalence.py
```

## Troubleshooting

If you get compilation errors:
- Ensure g++ is installed: `sudo apt-get install g++`
- Check that submodules are properly initialized

If you get Python import errors:
- Ensure you're using Python 3.12+: `python --version`
- Make sure uv sync completed successfully