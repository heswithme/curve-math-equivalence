#!/usr/bin/env python3
"""
Test math equivalence between Vyper and C++ implementations
"""

import ctypes
import subprocess
import os
from pathlib import Path
import tempfile

import boa


class MathTester:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.lib_path = None
        self._compile_cpp_lib()
        self._load_cpp_lib()
        self._deploy_vyper_contract()
    
    def _compile_cpp_lib(self):
        """Compile C++ wrapper to shared library"""
        print("Compiling C++ library...")
        
        wrapper_cpp = self.root_dir / "src" / "cpp_wrapper.cpp"
        self.lib_path = self.root_dir / "cpp_math.so"
        
        compile_cmd = [
            "g++", "-shared", "-fPIC", 
            "-o", str(self.lib_path),
            str(wrapper_cpp),
            "-O3", "-std=c++17",
            f"-I{self.root_dir}/cryptopool-simulator"
        ]
        
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"C++ compilation failed: {result.stderr}")
        
        print("✓ C++ library compiled")
    
    def _load_cpp_lib(self):
        """Load compiled C++ library"""
        self.cpp_lib = ctypes.CDLL(str(self.lib_path))
        
        # Define function signatures
        self.cpp_lib.python_newton_D_2.argtypes = [
            ctypes.c_longdouble, ctypes.c_longdouble,
            ctypes.c_longdouble, ctypes.c_longdouble,
            ctypes.c_longdouble
        ]
        self.cpp_lib.python_newton_D_2.restype = ctypes.c_longdouble
        
        self.cpp_lib.python_newton_y.argtypes = [
            ctypes.c_longdouble, ctypes.c_longdouble,
            ctypes.c_longdouble, ctypes.c_longdouble,
            ctypes.c_longdouble, ctypes.c_int
        ]
        self.cpp_lib.python_newton_y.restype = ctypes.c_longdouble
    
    def _deploy_vyper_contract(self):
        """Deploy Vyper StableswapMath contract"""
        print("Deploying Vyper contract...")
        
        contract_path = self.root_dir / "twocrypto-ng" / "contracts" / "main" / "StableswapMath.vy"
        
        with boa.env.prank("0x0000000000000000000000000000000000000001"):
            self.vyper_math = boa.load_partial(str(contract_path)).deploy()
        
        print("✓ Vyper contract deployed")
    
    def test_newton_D(self, A, x0, x1):
        """Test Newton_D equivalence"""
        # Vyper call
        xp = [x0, x1]
        vyper_D = self.vyper_math.newton_D(A, 145000000000000, xp)
        
        # C++ call (C++ expects raw A, so divide by 10000)
        cpp_D = self.cpp_lib.python_newton_D_2(
            ctypes.c_longdouble(A / 10000),
            ctypes.c_longdouble(145000000000000),
            ctypes.c_longdouble(x0),
            ctypes.c_longdouble(x1),
            ctypes.c_longdouble(x0 + x1)
        )
        cpp_D_int = int(cpp_D)
        
        rel_error = abs(vyper_D - cpp_D_int) / vyper_D if vyper_D > 0 else 0
        
        return vyper_D, cpp_D_int, rel_error
    
    def test_get_y(self, A, x0, x1, D, i):
        """Test get_y/newton_y equivalence"""
        # Vyper call
        xp = [x0, x1]
        vyper_y_result = self.vyper_math.get_y(A, 145000000000000, xp, D, i)
        vyper_y = vyper_y_result[0]
        
        # C++ call (C++ expects raw A, so divide by 10000)
        cpp_y = self.cpp_lib.python_newton_y(
            ctypes.c_longdouble(A / 10000),
            ctypes.c_longdouble(145000000000000),
            ctypes.c_longdouble(x0),
            ctypes.c_longdouble(x1),
            ctypes.c_longdouble(D),
            ctypes.c_int(i)
        )
        cpp_y_int = int(cpp_y)
        
        rel_error = abs(vyper_y - cpp_y_int) / vyper_y if vyper_y > 0 else 0
        
        return vyper_y, cpp_y_int, rel_error


def main():
    """Run equivalence tests"""
    print("=" * 80)
    print("Curve Math Equivalence Tests")
    print("=" * 80)
    
    # Initialize tester
    tester = MathTester()
    
    # Test cases
    scale = 10**18
    test_cases = [
        ("Equal balances", 400000, 1000000 * scale, 1000000 * scale),
        ("3:1 ratio", 400000, 500000 * scale, 1500000 * scale),
        ("19:1 ratio", 400000, 100000 * scale, 1900000 * scale),
        ("Low A", 100000, 1000000 * scale, 1000000 * scale),
        ("High A", 1600000, 1000000 * scale, 1000000 * scale),
    ]
    
    # Test Newton_D
    print("\n=== Newton_D Tests ===")
    print(f"{'Description':<20} {'Vyper D':<30} {'C++ D':<30} {'Rel Error':<15}")
    print("-" * 95)
    
    all_pass = True
    for desc, A, x0, x1 in test_cases:
        vyper_D, cpp_D, rel_error = tester.test_newton_D(A, x0, x1)
        pass_test = rel_error < 1e-15
        all_pass &= pass_test
        
        print(f"{desc:<20} {vyper_D:<30} {cpp_D:<30} {rel_error:<15.2e} {'✓' if pass_test else '✗'}")
    
    # Test get_y
    print("\n=== get_y Tests ===")
    print(f"{'Description':<20} {'i':<5} {'Vyper y':<30} {'C++ y':<30} {'Rel Error':<15}")
    print("-" * 100)
    
    for desc, A, x0, x1 in test_cases[:3]:  # Test first 3 cases
        # Get D first
        vyper_D, _, _ = tester.test_newton_D(A, x0, x1)
        
        for i in [0, 1]:
            vyper_y, cpp_y, rel_error = tester.test_get_y(A, x0, x1, vyper_D, i)
            pass_test = rel_error < 1e-15
            all_pass &= pass_test
            
            print(f"{desc:<20} {i:<5} {vyper_y:<30} {cpp_y:<30} {rel_error:<15.2e} {'✓' if pass_test else '✗'}")
    
    print("\n" + "=" * 80)
    if all_pass:
        print("✅ All tests passed! Math implementations are equivalent.")
        print("The A parameter can be deployed with confidence.")
    else:
        print("❌ Some tests failed.")
    
    # Clean up
    if tester.lib_path and tester.lib_path.exists():
        tester.lib_path.unlink()


if __name__ == "__main__":
    main()