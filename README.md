# llama-cpp RPM / Fedora COPR Packaging

RPM packaging for [`ggml-org/llama.cpp`](https://github.com/ggml-org/llama.cpp).

## Comparison to Fedora's official `llama-cpp`

Fedora's base repository package lags behind upstream and has a few architectural limitations that this package resolves:

1. **Full CPU SIMD Dispatch (`GGML_CPU_ALL_VARIANTS=ON`)**: The official Fedora package disables AVX/AVX2/AVX-512/FMA/F16C without enabling `GGML_BACKEND_DL`, forcing baseline x86-64 (SSE2) execution on CPU. This package builds all 14 x86-64 (or ARMv8/v9 / POWER / s390x / RISC-V) CPU backend variants and dynamically selects the fastest instruction set supported by the host CPU at runtime.
2. **Modular GPU Backend Plugins (`GGML_BACKEND_DL=ON`)**: The official Fedora package monolithically links ROCm (`libamdhip64`, `rocblas`, `hipblas`) into the base `llama-cpp` package (~216 MiB download plus gigabytes of ROCm dependencies even on Intel/NVIDIA machines) and omits Vulkan. This package compiles every GPU backend as an independent runtime plugin in its own subpackage.
3. **Out-of-the-Box Vulkan + Optional ROCm / CUDA / OpenCL / OpenBLAS**: `llama-cpp-backend-vulkan` is pulled in automatically via `Recommends:` (working on AMD, Intel, and NVIDIA GPUs with only the ~500 KB `vulkan-loader`). When `llama-cpp-backend-rocm` or `llama-cpp-backend-cuda` is also installed, `llama.cpp` automatically prefers `CUDA`/`ROCm` and deduplicates the same GPU by PCI bus ID so it is never double-allocated.
4. **Embedded Web UI Built Offline**: Pre-stages the release's matching `llama-bXXXX-ui.tar.gz` asset in `%prep` so `llama-server` includes the full Web UI while building 100% offline in `mock`/COPR chroots.
5. **Clean Upgrade Path (`1.0.0 > b9840`)**: Because RPM sorts digits newer than letters (`rpmdev-vercmp b9840 1.0.0` -> `b9840 < 1.0.0`), enabling this COPR cleanly upgrades existing Fedora `llama-cpp` installations without requiring an `Epoch`.

## Subpackage Layout

| Package | Contents | Dependency Behavior |
| :--- | :--- | :--- |
| `llama-cpp` | CLI binaries (`llama`, `llama-cli`, `llama-server`, `llama-bench`, `llama-mtmd-cli`, `llama-tts`, `llama-quantize`, `ggml-rpc-server`, etc.) with offline-embedded Web UI | Requires `llama-cpp-libs`; Recommends `numactl`; Suggests `ffmpeg-free` (for `mtmd` video input) |
| `llama-cpp-libs` | `/usr/lib64/libllama.so.1`, `/usr/lib64/libmtmd.so.1`, `/usr/lib64/libllama-common.so.1`, plus isolated `/usr/lib64/llama-cpp/libggml*.so.1` and all runtime-dispatched CPU SIMD variants (`libggml-cpu-*.so`) | Recommends `llama-cpp-backend-vulkan` |
| `llama-cpp-backend-vulkan` | `libggml-vulkan.so` (AMD, Intel, and NVIDIA GPUs via Vulkan) | Installed by default via `Recommends:` |
| `llama-cpp-backend-rocm` | `libggml-hip.so` (AMD ROCm / HIP backend, `x86_64`) | Auto-installed when `rocm-runtime` is present (`Supplements:`), or via `dnf install llama-cpp-backend-rocm` |
| `llama-cpp-backend-cuda` | `libggml-cuda.so` (NVIDIA CUDA backend; built when `--with cuda` is passed) | Auto-installed when NVIDIA CUDA driver libs are present (`Supplements:`), or via `dnf install llama-cpp-backend-cuda` |
| `llama-cpp-backend-opencl` | `libggml-opencl.so` (OpenCL backend, built with desktop `-DGGML_OPENCL_USE_ADRENO_KERNELS=OFF`) | Opt-in (`dnf install llama-cpp-backend-opencl`) so it does not conflict with Vulkan/CUDA/ROCm device enumeration |
| `llama-cpp-backend-blas` | `libggml-blas.so` (OpenBLAS backend) | Opt-in (`dnf install llama-cpp-backend-blas`) |
| `llama-cpp-devel` | Public headers (`llama.h`, `mtmd.h`, `ggml*.h`, `gguf.h`), `llama.pc`, and CMake configs | Requires `llama-cpp-libs` |

## Updating

Upstream tags stable releases as `vX.Y.Z` and attaches a `nightly-tag.txt` file containing the corresponding `bXXXX` build number.

To sync [`llama-cpp.spec`](llama-cpp.spec) with the latest upstream release:

```sh
./scripts/update-version.sh
# or via make:
make -f .copr/Makefile update
```

To pin a specific upstream release tag:

```sh
./scripts/update-version.sh llama-cpp.spec v1.0.0
```

