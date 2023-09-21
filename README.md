# gem5 Runahead
Implementing the HPCA'20 paper *Precise Runahead Execution (PRE)* in gem5

## Architecture Overview
![pre_arch](https://lshpku.github.io/gem5-runahead/pre_arch.svg)

## Usage
### Compile
* **IMPORTANT:** install SCons 4.3.0 (higher version will fail!)
  ```bash
  pip3 install scons==4.3.0
  ```
* Compile gem5
  ```bash
  cd gem5

  time scons build/RISCV/gem5.opt -j`nproc`
  # 6min51s on my 32-thread server
  ```

### New Params for PRE
All new params are defined under `BaseO3CPU`, as listed below:
| Name | Description | Default
| --- | --- | ---
| `enablePRE` | Enable Precise Runahead Execution | False
| `enablePREBranch` | Allow branch instructions in PRE | False
| `enablePREEarlyRecycle` | Enable register early recycle in PRE | False
| `numPRDQEntries` | Number of precise register deallocation queue entries | 192
| `numSSTEntries` | Number of stalling slice table entries | 128
| `enableMJ` | Enable my journal | False

### Run with Standard Config
I provide an O3CPU config `examples/three_level_o3.py` that resembles the model in the PRE paper.

* Run with PRE enabled
  ```bash
  build/RISCV/gem5.opt --outdir m5out-pre examples/three_level_o3.py \
      -p system.cpu.enablePRE=True \
      tests/test-progs/hello/bin/riscv/linux/hello
  # Hello world!
  ```
* Run without PRE
  ```bash
  build/RISCV/gem5.opt --outdir m5out-non examples/three_level_o3.py \
      tests/test-progs/hello/bin/riscv/linux/hello
  # Hello world!
  ```
* Print statistics
  ```bash
  # PRE
  cat m5out-pre/stats.txt | grep numCycles
  # system.cpu.numCycles  52698  # Number of cpu cycles simulated (Cycle)

  # No PRE
  cat m5out-non/stats.txt | grep numCycles
  # system.cpu.numCycles  52828  # Number of cpu cycles simulated (Cycle)
  ```

### How to Compile gem5 Faster
It's been proved that Clang-16 is faster than GCC-9 in more cases, so the way to compile gem5 faster is to use Clang!
* Get LLVM
  ```bash
  # Get LLVM 16.0.6 (stable)
  wget https://github.com/llvm/llvm-project/releases/download/llvmorg-16.0.6/llvm-project-16.0.6.src.tar.xz

  # Uncompress
  tar xf llvm-project-16.0.6.src.tar.xz

  # Rename
  mv llvm-project-16.0.6.src llvm-project
  ```
* Compile and install Clang and lld (a linker 10x faster than GNU ld)
  ```bash
  cd llvm-project

  # Note: change CMAKE_INSTALL_PREFIX if needed
  cmake -G Ninja -S llvm -B build          \
        -DLLVM_ENABLE_PROJECTS='clang;lld' \
        -DLLVM_INSTALL_UTILS=ON            \
        -DCMAKE_INSTALL_PREFIX=/usr/local  \
        -DCMAKE_BUILD_TYPE=Release

  time ninja -C build install
  # 13min43s on my 32-thread server
  ```
* **OPTIONAL:** Install PyPy (a python interpreter with JIT optimization)
  ```bash
  # Get PyPy 3.10
  wget https://downloads.python.org/pypy/pypy3.10-v7.3.12-linux64.tar.bz2

  # Uncompress
  tar xf pypy3.10-v7.3.12-linux64.tar.bz2

  # A safe way to use PyPy without overwriting your CPython
  export PATH=`pwd`/pypy3.10-v7.3.12-linux64/bin:$PATH
  export LD_LIBRARY_PATH=`pwd`/pypy3.10-v7.3.12-linux64/lib:$LD_LIBRARY_PATH

  # Install pip (note that `python3' now refers to pypy)
  python3 -m ensurepip

  # Install SCons again (cannot use CPython's SCons)
  pip3 install scons==4.3.0
  ```
* Compile gem5
  ```bash
  cd gem5

  time CXX=clang++ scons build/RISCV/gem5.opt -j`nproc` --linker=lld
  # 3min56s on my 32-thread server
  ```
* gem5 compile time comparison
  | Toolchain | Time (s) | Ratio
  | --- | --: | --:
  | GCC 9.4.0 | 411 | 100%
  | Clang 16.0.6 | 236 | 57%
  | Clang 16.0.6 + PyPy | 243 | 59%


## Presentation
**Implementation and Analysis of the Runahead-based Hardware Data Prefetching**  
Download: [runahead_implement_analysis.pdf](https://lshpku.github.io/gem5-runahead/runahead_implement_analysis.pdf)
![pre_thumb](https://lshpku.github.io/gem5-runahead/pre_thumb.jpg)
