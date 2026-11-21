# Upstream release version (vX.Y.Z) and its pinned nightly build tag (bXXXX).
# Each upstream vX.Y.Z release publishes a nightly-tag.txt asset naming the
# exact bXXXX build tag (which hosts the prebuilt Web UI asset and stamps
# LLAMA_BUILD_NUMBER / LLAMA_BUILD_COMMIT).
# Reference: https://github.com/ggml-org/ggml/discussions/1579
%global upstream_tag b12359
%global llama_build_number %(printf '%s' '%{upstream_tag}' | sed 's/^b//')
%global _privlibdir %{_libdir}/%{name}

# Compute backends (built as runtime dlopen() plugins via GGML_BACKEND_DL=ON)
%bcond_without vulkan
%bcond_without opencl
%bcond_without blas
%bcond_without rpc
%ifarch x86_64
%bcond_without rocm
%else
%bcond_with rocm
%endif
# Proprietary NVIDIA CUDA toolkit (requires external NVIDIA CUDA repo in COPR)
%bcond_with cuda
# Optional full upstream CTest suite (smoke tests always run in %%check)
%bcond_with tests

%if %{with rocm}
%{!?amdgpu_targets:%global amdgpu_targets %{?rocm_gpu_list_default}%{!?rocm_gpu_list_default:gfx906;gfx908;gfx90a;gfx942;gfx1030;gfx1100;gfx1101;gfx1102;gfx1150;gfx1151;gfx1200;gfx1201}}
%endif

Name:           llama-cpp
Version:        1.0.0
Release:        %autorelease
Summary:        LLM inference engine in C/C++
# Core llama.cpp & ggml: MIT (with Apache-2.0 llamafile sgemm kernels)
# Vendored headers: nlohmann-json (MIT), cpp-httplib (MIT), miniaudio/stb/sheredom (MIT-0 OR Unlicense)
License:        MIT AND Apache-2.0 AND (MIT-0 OR Unlicense)
URL:            https://github.com/ggml-org/llama.cpp
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/llama.cpp-%{version}.tar.gz
# Prebuilt Web UI assets from the pinned bXXXX release tag, staged offline in
# %%prep so CMake embeds them without network access in mock/COPR buildroots.
Source1:        %{url}/releases/download/%{upstream_tag}/llama-%{upstream_tag}-ui.tar.gz

ExclusiveArch:  x86_64 aarch64 ppc64le s390x riscv64

BuildRequires:  cmake >= 3.21
BuildRequires:  gcc-c++
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(openssl)

%if %{with vulkan}
BuildRequires:  glslc
BuildRequires:  spirv-headers-devel
BuildRequires:  vulkan-devel
%endif

%if %{with opencl}
BuildRequires:  OpenCL-ICD-Loader-devel
BuildRequires:  opencl-headers
BuildRequires:  python3
%endif

%if %{with blas}
BuildRequires:  openblas-devel
%endif

%if %{with rocm}
BuildRequires:  hipblas-devel
BuildRequires:  rocblas-devel
BuildRequires:  rocm-comgr-devel
BuildRequires:  rocm-hip-devel
BuildRequires:  rocm-rpm-macros
BuildRequires:  rocm-runtime-devel
%endif

%if %{with cuda}
BuildRequires:  cuda-toolkit
%endif

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Recommends:     numactl
# Used by libmtmd via subprocess for multimodal video input decoding
Suggests:       ffmpeg-free

%description
llama.cpp provides LLM and multimodal inference in C/C++ with minimal
dependencies and broad hardware support via runtime-loaded compute backends.

This package contains the command-line tools, including the unified llama
binary, llama-cli, llama-server (with embedded Web UI and HTTPS client
support), llama-bench, llama-mtmd-cli, llama-tts, and llama-quantize.

%package libs
Summary:        Core shared libraries and CPU compute backends for %{name}
Provides:       bundled(cpp-httplib)
Provides:       bundled(ggml) = %{version}
Provides:       bundled(miniaudio)
Provides:       bundled(nlohmann-json)
Provides:       bundled(stb)
%if %{with vulkan}
Recommends:     %{name}-backend-vulkan%{?_isa} = %{version}-%{release}
%endif

%description libs
Core shared libraries (libllama, libmtmd, libggml) and dynamically loaded CPU
SIMD backend variants for %{name}. Internal ggml libraries and compute backend
plugins are isolated in %{_privlibdir} to avoid conflicts with other ggml
consumers.

%if %{with vulkan}
%package backend-vulkan
Summary:        Vulkan GPU compute backend for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       vulkan-loader%{?_isa}

%description backend-vulkan
Dynamically loaded Vulkan compute backend plugin (libggml-vulkan.so) for
%{name}, supporting AMD, Intel, and NVIDIA GPUs out of the box.
%endif

%if %{with rocm}
%package backend-rocm
Summary:        AMD ROCm / HIP GPU compute backend for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Supplements:    (%{name}-libs%{?_isa} and rocm-runtime)

%description backend-rocm
Dynamically loaded AMD ROCm / HIP compute backend plugin (libggml-hip.so) for
%{name}.
%endif

%if %{with opencl}
%package backend-opencl
Summary:        OpenCL GPU compute backend for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description backend-opencl
Dynamically loaded OpenCL compute backend plugin (libggml-opencl.so) for
%{name}. Install this subpackage only when targeting an OpenCL-only accelerator
not covered by Vulkan, ROCm, or CUDA.
%endif

%if %{with blas}
%package backend-blas
Summary:        OpenBLAS CPU acceleration backend for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description backend-blas
Dynamically loaded OpenBLAS compute backend plugin (libggml-blas.so) for
%{name}.
%endif

%if %{with cuda}
%package backend-cuda
Summary:        NVIDIA CUDA GPU compute backend for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Supplements:    (%{name}-libs%{?_isa} and (xorg-x11-drv-nvidia-cuda-libs or nvidia-driver-cuda-libs))

%description backend-cuda
Dynamically loaded NVIDIA CUDA compute backend plugin (libggml-cuda.so) for
%{name}.
%endif

%package devel
Summary:        Development headers and CMake config files for %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description devel
Header files, pkg-config specification, and CMake package configuration files
for developing applications against libllama and libmtmd.

%prep
%autosetup -p1 -n llama.cpp-%{version}

# Pre-stage the prebuilt Web UI assets into tools/ui/dist so scripts/ui-assets.cmake
# takes its local pre-built asset path (priority 1) and never attempts network
# downloads during %%build.
mkdir -p tools/ui/dist
tar -xzf %{SOURCE1} -C tools/ui/dist --strip-components=1
printf '{"version":"%s"}\n' '%{llama_build_number}' > tools/ui/dist/build.json

%build
%if %{with cuda}
export PATH="${PATH}:/usr/local/cuda/bin"
%endif

%cmake \
    -DGIT_EXE=OFF \
    -DBUILD_SHARED_LIBS=ON \
    -DLLAMA_BUILD_IS_DEV=OFF \
    -DLLAMA_BUILD_NUMBER=%{llama_build_number} \
    -DLLAMA_BUILD_COMMIT=%{upstream_tag} \
    -DLLAMA_USE_PREBUILT_UI=OFF \
    -DLLAMA_BUILD_UI=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
%if %{with tests}
    -DLLAMA_BUILD_TESTS=ON \
    -DLLAMA_TESTS_INSTALL=OFF \
%else
    -DLLAMA_BUILD_TESTS=OFF \
%endif
    -DLLAMA_OPENSSL=ON \
    -DLLAMA_SUBPROCESS=ON \
    -DGGML_CCACHE=OFF \
    -DGGML_OPENMP=ON \
    -DGGML_NATIVE=OFF \
    -DGGML_BACKEND_DL=ON \
    -DGGML_CPU_ALL_VARIANTS=ON \
    -DGGML_BACKEND_DIR=%{_privlibdir} \
    -DCMAKE_INSTALL_RPATH=%{_privlibdir} \
%if %{with vulkan}
    -DGGML_VULKAN=ON \
%endif
%if %{with opencl}
    -DGGML_OPENCL=ON \
    -DGGML_OPENCL_USE_ADRENO_KERNELS=OFF \
%endif
%if %{with blas}
    -DGGML_BLAS=ON \
    -DGGML_BLAS_VENDOR=OpenBLAS \
    -DBLAS_INCLUDE_DIRS=%{_includedir}/openblas \
%endif
%if %{with rpc}
    -DGGML_RPC=ON \
%endif
%if %{with rocm}
    -DGGML_HIP=ON \
    -DAMDGPU_TARGETS="%{amdgpu_targets}" \
%endif
%if %{with cuda}
    -DGGML_CUDA=ON \
    -DCMAKE_CUDA_FLAGS="-Xcompiler -fPIC" \
    %{?cuda_archs:-DCMAKE_CUDA_ARCHITECTURES="%{cuda_archs}"} \
%endif
    %{nil}

%cmake_build

%install
%cmake_install

# Public llama.cpp libraries (libllama.so.1, libmtmd.so.1, libllama-common.so.1)
# remain in standard %%{_libdir} so external applications linking -lllama work
# without custom RPATHs. Move internal bundled libggml*.so.* and unversioned
# CLI implementation libraries (libllama-*-impl.so) into %%{_privlibdir} so
# libggml never collides with other packages (such as whisper-cpp).
mkdir -p %{buildroot}%{_privlibdir}
mv %{buildroot}%{_libdir}/libggml*.so.* %{buildroot}%{_privlibdir}/
find %{buildroot}%{_libdir} -maxdepth 1 -type f -name 'libllama-*-impl.so' \
    -exec mv -t %{buildroot}%{_privlibdir}/ {} +

# Repoint libggml*.so development symlinks in %%{_libdir} to %%{_privlibdir}
for link in %{buildroot}%{_libdir}/libggml*.so; do
    target=$(readlink "${link}")
    ln -sf "%{name}/${target}" "${link}"
done

# Ensure pkg-config callers also search %%{_privlibdir} for -lggml / -lggml-base
sed -i 's|-L${libdir}|-L${libdir} -L${libdir}/%{name} -Wl,-rpath,${libdir}/%{name}|' \
    %{buildroot}%{_libdir}/pkgconfig/llama.pc

# Remove Python conversion scripts from bindir if installed
rm -f %{buildroot}%{_bindir}/convert*.py

%check
# Smoke-test dynamic linker resolution, CPU backend plugin dlopen() scoring,
# and embedded version metadata (running from %%{_privlibdir} so ggml finds the
# staged backend plugins prior to system installation).
(
    cd %{buildroot}%{_privlibdir}
    export LD_LIBRARY_PATH="%{buildroot}%{_libdir}:%{buildroot}%{_privlibdir}"
    %{buildroot}%{_bindir}/llama-cli --version
    %{buildroot}%{_bindir}/llama-server --version
)
%if %{with tests}
%ctest
%endif

%files
%license LICENSE licenses/*
%doc README.md
%{_bindir}/llama*
%if %{with rpc}
%{_bindir}/ggml-rpc-server
%endif

%files libs
%license LICENSE licenses/*
%{_libdir}/libllama.so.1*
%{_libdir}/libllama-common.so.1*
%{_libdir}/libmtmd.so.1*
%dir %{_privlibdir}
%{_privlibdir}/libllama-*-impl.so*
%{_privlibdir}/libggml.so.1*
%{_privlibdir}/libggml-base.so.1*
%{_privlibdir}/libggml-cpu*.so*
%if %{with rpc}
%{_privlibdir}/libggml-rpc.so*
%endif

%if %{with vulkan}
%files backend-vulkan
%{_privlibdir}/libggml-vulkan.so*
%endif

%if %{with rocm}
%files backend-rocm
%{_privlibdir}/libggml-hip.so*
%endif

%if %{with opencl}
%files backend-opencl
%{_privlibdir}/libggml-opencl.so*
%endif

%if %{with blas}
%files backend-blas
%{_privlibdir}/libggml-blas.so*
%endif

%if %{with cuda}
%files backend-cuda
%{_privlibdir}/libggml-cuda.so*
%endif

%files devel
%{_includedir}/llama*.h
%{_includedir}/ggml*.h
%{_includedir}/gguf.h
%{_includedir}/mtmd*.h
%{_libdir}/lib*.so
%{_libdir}/cmake/llama/
%{_libdir}/cmake/ggml/
%{_libdir}/pkgconfig/llama.pc

%changelog
%autochangelog
