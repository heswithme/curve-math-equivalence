#define PYTHON_WRAPPER 1
#include "../cryptopool-simulator/main-stableswap.cpp"

extern "C" {
    // Wrapper that adjusts A by dividing by 10000 before passing to original function
    money python_newton_D_2(money A, money gamma, money x0, money x1, money D0) {
        money x[2] = {x0, x1};
        // Divide A by 10000 to match Vyper's expectation
        return newton_D_2(A / 10000.0L, gamma, x, D0);
    }
    
    // Wrapper for newton_y
    money python_newton_y(money A, money gamma, money x0, money x1, money D, int i) {
        money x[2] = {x0, x1};
        // Divide A by 10000 to match Vyper's expectation
        return newton_y(A / 10000.0L, gamma, x, 2, D, i);
    }
}