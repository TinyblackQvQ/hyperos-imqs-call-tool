from datetime import datetime
import os
from pathlib import Path
import posixpath
import shlex
import stat
import subprocess
import time

import adbutils
from Command import Command, parse_command

#### Device paths

### path of program runtime files storage on device
DEVICE_RUNTIME_PATH = os.getenv("RUNTIME_PATH", "/sdcard/Download/debug/")
## Log file on device
DEVICE_LOG_FILE_PATH = f"{DEVICE_RUNTIME_PATH}log.txt"
### KernelSU path on device
DEVICE_KERNELSU_PATH = os.getenv("KERNELSU_PATH", "/data/adb/")
## kernelsu deamon executable file on device
DEVICE_KSU_DEAMON = f"{DEVICE_KERNELSU_PATH}ksud"

#### Local paths

### path of flash tools, like adb, fastboot 
FLASHTOOL_PATH = os.getenv("FLASHTOOL_PATH", f"{os.getcwd()}/runtime/flashtool/")
## fastboot exe file
FASTBOOT = f"{FLASHTOOL_PATH}fastboot.exe"
## timeout for waiting a device enter fastboot mode
FASTBOOT_WAIT_TIMEOUT_SECONDS = int(os.getenv("FASTBOOT_WAIT_TIMEOUT_SECONDS", "30"))
### path of unlock efi file
EFI_FILE_PATH = os.getenv("EFI_FILE_PATH", f"{os.getcwd()}/runtime/efi/gbl_efi_unlock.efi")
### path of ksu files
KSU_PATH = os.getenv("KSU_PATH", f"{os.getcwd()}/runtime/ksu/")
## kernelsu apk file
KSU_APK = f"{KSU_PATH}kernelsu.apk"
## kernelsu deamon executable file
KSU_DEAMON_FILE_PATH = f"{KSU_PATH}ksud"

HELP_STR = """---------------------
HyperOS IMQSNative Service Call Tool
---------------------
This tool can run any command & get its execution results via miui.mqsas.IMQSNative, which have a bug could let user run command with system permission;
This bug only works on system which don't have 2026.2 security patch fix;
If your device's system is above 3.0.6 (for older devices like Xiaomi 13 & Redmi K70) ~ 3.0.22 (for newer devices like Xiaomi 17 & Redmi K90 Pro Max), you may cannot use this tool.
This bug need permissive selinux, you need to run "~selinux down" before run any command;
Take full responsibility for your own device! Your data is priceless! Strongly recommend you to backup your data before doing any dangerous operation.
---------------------
~bootloader \t\t\t [CPU Snapdragon 8 Elite Gen 5 (Xiaomi 17 Series & Redmi K90 Pro Max) Only!!! Don't run this on other devices]
\t\t\t\t Try unlock the device's bootloader with unlock efi file @https://github.com/hicode002/qualcomm_gbl_exploit_poc
~ksu \t\t\t\t [install/uninstall/init(Default)] Operations about manage KernelSU:
\t\t\t\t install - [TODO] try install KernelSU and prepare related files on your device
\t\t\t\t uninstall - [TODO] try to uninstall KernelSU and related files from your device (!!! Won't keep your perferences!!!)
\t\t\t\t init - try call up KernelSU service on an already installed device
~selinux [up/down] \t\t Try to set selinux permissive/forced
---------------------
cls \t\t\t\t Clear screen
debug \t\t\t\t Switch tool Debug mode, when True, it will display detailed running info 
devices \t\t\t Get connected devices' info
help \t\t\t\t Show this help message
safe \t\t\t\t Switch tool Safe Mode, when True, it prohibits some dangerous operations like "rm"
pull [SRC_DIR] [LOCAL_TARGET_DIR] Pull file or directory from device to local target dir
push [LOCAL_SRC_DIR] [TARGET_DIR] Push local file or directory to device target dir
shell [COMMAND] \t\t Run a command with adb shell
switch [SERIAL] \t\t Switch to a specific device
*[services] *[args] \t\t Run a command with IMQSNative service
---------------------"""

adb = adbutils.adb


def generate_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(content: str, debug_mode: bool):
    if debug_mode:
        print(f"[{generate_timestamp()}] [DEBUG] {content}")


def quote_remote_path(path: str) -> str:
    return shlex.quote(normalize_remote_path(path))


def escape_shell_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_shell_cmd(cmd: Command, log_path: str = DEVICE_LOG_FILE_PATH) -> str:
    return (
        'service call miui.mqsas.IMQSNative 21 '
        f'i32 1 s16 "{escape_shell_string(cmd.service)}" '
        f'i32 1 s16 "{escape_shell_string(cmd.args)}" '
        f's16 "{escape_shell_string(log_path)}" i32 60'
    )


def run_shell_cmd(
    device: adbutils.AdbDevice,
    cmd: Command,
    debug_mode: bool,
    log_path: str = DEVICE_LOG_FILE_PATH,
) -> str:
    log_path = normalize_remote_path(log_path)
    log_dir = posixpath.dirname(log_path) or "/"
    # create debug dir
    device.shell(f"mkdir -p {quote_remote_path(log_dir)}")
    # clear older log
    device.shell(f"rm {quote_remote_path(log_path)}")
    # run shell command
    shell_cmd = build_shell_cmd(cmd, log_path=log_path)
    log(f"Running command: {shell_cmd}", debug_mode)
    result = device.shell(shell_cmd)
    log(f"Result: {result}", debug_mode)
    # print result
    result = device.shell(f"cat {quote_remote_path(log_path)}")
    return result


def normalize_remote_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    return normalized or "/"


def join_remote_path(base: str, *parts: str) -> str:
    base = normalize_remote_path(base)
    if base == "/":
        return posixpath.join("/", *parts)
    return posixpath.join(base.rstrip("/"), *parts)


def get_remote_name(path: str) -> str:
    normalized = normalize_remote_path(path).rstrip("/")
    name = posixpath.basename(normalized)
    return name or "root"


def make_remote_dir(device: adbutils.AdbDevice, remote_dir: str):
    device.shell(f"mkdir -p {quote_remote_path(remote_dir)}")


def ensure_fastboot_available():
    if not Path(FASTBOOT).is_file():
        raise FileNotFoundError(f"Fastboot tool not found: {FASTBOOT}")


def run_fastboot_command(
    args: list[str], debug_mode: bool, timeout: int = 15
) -> subprocess.CompletedProcess[str]:
    ensure_fastboot_available()
    command = [FASTBOOT, *args]
    log(f"Running fastboot command: {' '.join(command)}", debug_mode)
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    if result.stdout.strip():
        log(f"fastboot stdout: {result.stdout.strip()}", debug_mode)
    if result.stderr.strip():
        log(f"fastboot stderr: {result.stderr.strip()}", debug_mode)
    return result


def wait_for_fastboot_device(debug_mode: bool) -> list[str]:
    deadline = time.monotonic() + FASTBOOT_WAIT_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        result = run_fastboot_command(["devices"], debug_mode, timeout=5)
        devices = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if devices:
            return devices
        time.sleep(1)

    raise TimeoutError(
        f"Timed out after {FASTBOOT_WAIT_TIMEOUT_SECONDS}s waiting for a fastboot device."
    )


def push_path(
    device: adbutils.AdbDevice, local_src: str, remote_target_dir: str, debug_mode: bool
) -> tuple[str, int]:
    src_path = Path(local_src).expanduser().resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Local path does not exist: {src_path}")

    make_remote_dir(device, remote_target_dir)

    if src_path.is_file():
        remote_path = join_remote_path(remote_target_dir, src_path.name)
        log(f"Pushing file {src_path} -> {remote_path}", debug_mode)
        size = device.sync.push(src_path, remote_path)
        return remote_path, size

    remote_root = join_remote_path(remote_target_dir, src_path.name)
    total_size = 0
    for current_root, _, files in os.walk(src_path):
        relative_root = Path(current_root).relative_to(src_path)
        remote_dir = (
            remote_root
            if str(relative_root) == "."
            else join_remote_path(remote_root, relative_root.as_posix())
        )
        make_remote_dir(device, remote_dir)

        for file_name in files:
            local_file = Path(current_root) / file_name
            remote_file = join_remote_path(remote_dir, file_name)
            log(f"Pushing file {local_file} -> {remote_file}", debug_mode)
            total_size += device.sync.push(local_file, remote_file)

    return remote_root, total_size


def pull_path(device: adbutils.AdbDevice, remote_src: str, local_target_dir: str) -> Path:
    remote_src = normalize_remote_path(remote_src)
    local_target = Path(local_target_dir).expanduser().resolve()
    local_target.mkdir(parents=True, exist_ok=True)

    remote_info = device.sync.stat(remote_src)
    destination = local_target / get_remote_name(remote_src)

    if stat.S_ISDIR(remote_info.mode):
        device.sync.pull(remote_src, destination, exist_ok=True)
    else:
        device.sync.pull(remote_src, destination)

    return destination


def main():
    debug_mode = False
    safe_mode = True
    curr_device = None
    print(HELP_STR)
    while 1:
        try:
            # try connect to the default device
            if curr_device is None:
                try:
                    curr_device = adb.device()
                except:
                    print("No device connected")
                    input("Press enter to recheck devices.")
                    continue

            cmd = parse_command(
                input(f"[{generate_timestamp()}] ({curr_device.serial}) > ")
            )
            if cmd.service == "":
                continue
            cmd.service = cmd.service.lower()

            if cmd.service == "help":
                print(HELP_STR)

            elif cmd.service == "debug":
                debug_mode = not debug_mode
                print(f"DebugMode: {debug_mode}")

            elif cmd.service == "safe":
                safe_mode = not safe_mode
                print(f"SafeMode: {safe_mode}")

            elif cmd.service == "cls":
                os.system("cls")

            elif cmd.service == "switch":
                if cmd.args:
                    curr_device = adb.device(serial=cmd.args)
                    print(
                        f"Connected to device {curr_device.serial}:{curr_device.prop.model}"
                    )
                else:
                    print("Please specify device serial")

            elif cmd.service == "devices":
                devices = adb.device_list()
                if devices:
                    print("Connected Devices:")
                    for i, d in enumerate(devices):
                        print(f"{i}: {d.serial} - {d.prop.model}")
                else:
                    print("No devices connected")

            elif cmd.service == "~selinux":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                if cmd.args == "up":
                    print(run_shell_cmd(curr_device, Command("setenforce", "1"), debug_mode))
                    continue
                elif cmd.args == "down":
                    ensure_fastboot_available()
                    print(curr_device.shell("reboot bootloader"))
                    wait_for_fastboot_device(debug_mode)
                    result = run_fastboot_command(
                        ["oem", "set-gpu-preemption-value", "0", "androidboot.selinux=permissive"],
                        debug_mode,
                    )
                    if result.stdout.strip():
                        print(result.stdout.strip())
                    time.sleep(1)
                    result = run_fastboot_command(["continue"], debug_mode)
                    if result.stdout.strip():
                        print(result.stdout.strip())
                    input("Please wait your device reboot...(Press Enter to continue)")
                else:
                    print("Usage: ~selinux [up/down]")

            elif cmd.service == "~bootloader":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                curr_device.sync.push(EFI_FILE_PATH, f"{DEVICE_RUNTIME_PATH}efi_unlock.efi")
                time.sleep(5)
                print(
                    run_shell_cmd(
                        curr_device,
                        Command(
                            "dd",
                            f"if={DEVICE_RUNTIME_PATH}efi_unlock.efi of=/dev/block/by-name/efisp",
                        ),
                        debug_mode,
                    )
                )
                curr_device.shell("reboot")
                input("Please wait your device reboot...(Press Enter to continue)")
            
            elif cmd.service == "~ksu":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                if cmd.args == "init":
                    print(run_shell_cmd(curr_device, Command(f"{DEVICE_KSU_DEAMON}", "late-load"), debug_mode))
                elif cmd.args == "install" or cmd.args == "uninstall":
                    print("Not implemented for now, please check for a newer version of the tool.")
                else:
                    print("Invalid argument.")
            
            elif cmd.service == "shell":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                result = curr_device.shell(cmd.args)
                print(result)

            elif cmd.service == "push":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                if len(cmd.argv) != 2:
                    print("Usage: push [LOCAL_SRC_DIR] [TARGET_DIR]")
                    continue

                remote_path, total_size = push_path(
                    curr_device, cmd.argv[0], cmd.argv[1], debug_mode
                )
                print(f"Pushed to {remote_path} ({total_size} bytes)")

            elif cmd.service == "pull":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                if len(cmd.argv) != 2:
                    print("Usage: pull [SRC_DIR] [LOCAL_TARGET_DIR]")
                    continue

                local_path = pull_path(curr_device, cmd.argv[0], cmd.argv[1])
                print(f"Pulled to {local_path}")

            elif cmd.service == "rm":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                if not safe_mode:
                    # check if command dangerous
                    if (
                        cmd.args
                        and "-rf" in cmd.args
                        and ("*" in cmd.args or "/" in cmd.args)
                    ):
                        print("WARNING: This operation might be dangerous!")
                        confirm = input("Are you sure? (yes/no): ")
                        if confirm.lower() == "yes":
                            print(run_shell_cmd(curr_device, cmd, debug_mode))
                        else:
                            print("Operation cancelled")
                    else:
                        print(run_shell_cmd(curr_device, cmd, debug_mode))
                else:
                    print("Cannot do this operation when safe mode is on!")

            else:
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                print(run_shell_cmd(curr_device, cmd, debug_mode))

        except KeyboardInterrupt:
            print("Exiting...")
            exit()

        except adbutils.AdbError as e:
            print(f"AdbError:{e}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
