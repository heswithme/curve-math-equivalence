#define PYTHON_WRAPPER 1
#include "../cryptopool-simulator/main-stableswap.cpp"

extern "C" {
    // Wrapper for newton_D_2
    money python_newton_D_2(money A, money gamma, money x0, money x1, money D0) {
        money x[2] = {x0, x1};
        return newton_D_2(A, gamma, x, D0);
    }
    
    // Wrapper for newton_y
    money python_newton_y(money A, money gamma, money x0, money x1, money D, int i) {
        money x[2] = {x0, x1};
        return newton_y(A, gamma, x, 2, D, i);
    }
}