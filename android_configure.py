#!/usr/bin/env python3
import platform
import sys
import os

# ============================================================
# Patch helper
# ============================================================
def patch_android():
    print("- Patches List -")
    print("[1] deps/v8/src/trap-handler/trap-handler.h")
    if platform.system() == "Linux":
        os.system(
            "patch -f ./deps/v8/src/trap-handler/trap-handler.h "
            "< ./android-patches/trap-handler.h.patch"
        )
    print("\033[92mInfo:\033[0m Patch attempted.")

# ============================================================
# Platform check
# ============================================================
if platform.system() == "Windows":
    print("android-configure is not supported on Windows.")
    sys.exit(1)

# ============================================================
# Patch mode
# ============================================================
if len(sys.argv) == 2 and sys.argv[1] == "patch":
    patch_android()
    sys.exit(0)

# ============================================================
# Args validation
# ============================================================
if len(sys.argv) != 4:
    print("Usage: ./android-configure <ndk-path> <android-api> <arch>")
    sys.exit(1)

android_ndk_path = sys.argv[1]
android_sdk_version = sys.argv[2]
arch = sys.argv[3]

if not os.path.isdir(android_ndk_path):
    print("\033[91mError:\033[0m Invalid Android NDK path")
    sys.exit(1)

if int(android_sdk_version) < 24:
    print("\033[91mError:\033[0m Android API must be >= 24")
    sys.exit(1)

# ============================================================
# Architecture mapping
# ============================================================
if arch == "arm":
    DEST_CPU = "arm"
    TOOLCHAIN_PREFIX = "armv7a-linux-androideabi"
elif arch in ("aarch64", "arm64"):
    DEST_CPU = "arm64"
    TOOLCHAIN_PREFIX = "aarch64-linux-android"
    arch = "arm64"
elif arch == "x86":
    DEST_CPU = "ia32"
    TOOLCHAIN_PREFIX = "i686-linux-android"
elif arch == "x86_64":
    DEST_CPU = "x64"
    TOOLCHAIN_PREFIX = "x86_64-linux-android"
    arch = "x64"
else:
    print("\033[91mError:\033[0m Unsupported architecture")
    sys.exit(1)

print("\033[92mInfo:\033[0m Target CPU:", DEST_CPU)

# ============================================================
# Host OS + toolchain
# ============================================================
if platform.system() == "Linux":
    host_os = "linux"
    toolchain_path = f"{android_ndk_path}/toolchains/llvm/prebuilt/linux-x86_64"
elif platform.system() == "Darwin":
    host_os = "darwin"
    toolchain_path = f"{android_ndk_path}/toolchains/llvm/prebuilt/darwin-x86_64"
else:
    print("\033[91mError:\033[0m Unsupported host OS")
    sys.exit(1)

# ============================================================
# Compiler environment
# ============================================================
os.environ["PATH"] += os.pathsep + toolchain_path + "/bin"

os.environ["CC"] = (
    f"{toolchain_path}/bin/{TOOLCHAIN_PREFIX}{android_sdk_version}-clang"
)
os.environ["CXX"] = (
    f"{toolchain_path}/bin/{TOOLCHAIN_PREFIX}{android_sdk_version}-clang++"
)

# Host compiler (for build tools)
os.environ["CC_host"] = os.popen("command -v clang || command -v gcc").read().strip()
os.environ["CXX_host"] = os.popen("command -v clang++ || command -v g++").read().strip()

# ============================================================
# GYP_DEFINES  (CRITICAL PART)
# ============================================================
GYP_DEFINES = [
    f"target_arch={arch}",
    f"v8_target_arch={arch}",
    f"android_target_arch={arch}",
    f"host_os={host_os}",
    "OS=android",

    # Android paths
    f"ANDROID_NDK_ROOT={android_ndk_path}",
    f"ANDROID_NDK_SYSROOT={toolchain_path}/sysroot",

    # ---- HARD DISABLE INSPECTOR ----
    "v8_enable_inspector=0",
    "v8_enable_inspector_support=0",
    "v8_enable_websockets=0",
    "v8_enable_debugging_features=0",

    # ---- Disable unused tracing ----
    "node_use_dtrace=false",
]

os.environ["GYP_DEFINES"] = " ".join(GYP_DEFINES)

print("\033[92mInfo:\033[0m GYP_DEFINES:")
for d in GYP_DEFINES:
    print("   ", d)

# ============================================================
# Run configure
# ============================================================
if not os.path.exists("./configure"):
    print("\033[91mError:\033[0m ./configure not found")
    sys.exit(1)

cmd = (
    "./configure "
    f"--dest-cpu={DEST_CPU} "
    "--dest-os=android "
    "--cross-compiling "
    "--with-intl=none "
    "--openssl-no-asm "
    "--without-inspector "
)

print("\033[92mInfo:\033[0m Running configure:")
print(cmd)

ret = os.system(cmd)
sys.exit(ret)