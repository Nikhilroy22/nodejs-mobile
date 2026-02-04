import platform
import sys
import os

def patch_android():
    print("- Patches List -")
    print("[1] [deps/v8/src/trap-handler/trap-handler.h] related to https://github.com/nodejs/node/issues/36287")
    if platform.system() == "Linux":
        os.system(
            "patch -f ./deps/v8/src/trap-handler/trap-handler.h "
            "< ./android-patches/trap-handler.h.patch"
        )
    print("\033[92mInfo:\033[0m Tried to patch.")

# -------------------------
# Platform check
# -------------------------
if platform.system() == "Windows":
    print("android-configure is not supported on Windows yet.")
    sys.exit(1)

# -------------------------
# Patch mode
# -------------------------
if len(sys.argv) == 2 and sys.argv[1] == "patch":
    patch_android()
    sys.exit(0)

# -------------------------
# Args validation
# -------------------------
if len(sys.argv) != 4:
    print("Usage: ./android-configure <path-to-ndk> <android-sdk-version> <arch>")
    sys.exit(1)

android_ndk_path = sys.argv[1]
android_sdk_version = sys.argv[2]
arch = sys.argv[3]

if not os.path.exists(android_ndk_path):
    print("\033[91mError:\033[0m Invalid Android NDK path")
    sys.exit(1)

if int(android_sdk_version) < 24:
    print("\033[91mError:\033[0m Android SDK version must be >= 24")
    sys.exit(1)

# -------------------------
# Architecture mapping
# -------------------------
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
    print("\033[91mError:\033[0m Invalid architecture")
    sys.exit(1)

print("\033[92mInfo:\033[0m Configuring for", DEST_CPU)

# -------------------------
# Host OS + toolchain
# -------------------------
if platform.system() == "Linux":
    host_os = "linux"
    toolchain_path = android_ndk_path + "/toolchains/llvm/prebuilt/linux-x86_64"
elif platform.system() == "Darwin":
    host_os = "darwin"
    toolchain_path = android_ndk_path + "/toolchains/llvm/prebuilt/darwin-x86_64"
else:
    print("\033[91mError:\033[0m Unsupported host OS")
    sys.exit(1)

# -------------------------
# Compiler env
# -------------------------
os.environ["PATH"] += os.pathsep + toolchain_path + "/bin"

os.environ["CC"] = (
    f"{toolchain_path}/bin/{TOOLCHAIN_PREFIX}{android_sdk_version}-clang"
)
os.environ["CXX"] = (
    f"{toolchain_path}/bin/{TOOLCHAIN_PREFIX}{android_sdk_version}-clang++"
)

# host compiler (for tools run on build machine)
os.environ["CC_host"] = os.popen("command -v gcc").read().strip()
os.environ["CXX_host"] = os.popen("command -v g++").read().strip()

# -------------------------
# GYP_DEFINES (VERY IMPORTANT)
# -------------------------
GYP_DEFINES = []
GYP_DEFINES.append(f"target_arch={arch}")
GYP_DEFINES.append(f"v8_target_arch={arch}")
GYP_DEFINES.append(f"android_target_arch={arch}")
GYP_DEFINES.append(f"host_os={host_os}")
GYP_DEFINES.append("OS=android")
GYP_DEFINES.append(f"ANDROID_NDK_ROOT={android_ndk_path}")
GYP_DEFINES.append(f"ANDROID_NDK_SYSROOT={toolchain_path}/sysroot")

os.environ["GYP_DEFINES"] = " ".join(GYP_DEFINES)

# -------------------------
# Run configure (NO --shared)
# -------------------------
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
    "--disable-tests"
)
print("\033[92mInfo:\033[0m Running:", cmd)
ret = os.system(cmd)
sys.exit(ret)