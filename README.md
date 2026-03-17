> README in [简体中文](./docs/README.zh_cn.md)

## HyperOS IMQSNative Service Call Tool

This tool can run any command & get its execution results via miui.mqsas.IMQSNative, which have a bug could let user run command with system permission;

This bug only works on system which don't have 2026.2 security patch fix;

If your device's system is above 3.0.6 (for older devices like Xiaomi 13 & Redmi K70) ~ 3.0.22 (for newer devices like Xiaomi 17 & Redmi K90 Pro Max), you may cannot use this tool.

This bug need permissive selinux, you need to run "`~selinux down`" before run any command;
You can try unlock the bootloader on 8 Elite Gen 5 devices (Xiaomi 17 series & Redmi K90 Pro Max) with command "~bootloader";
Take full responsibility for your own device! Your data is priceless! Strongly recommend you to backup your data before doing any dangerous operation.

The efi unlock file was written & build by [@hicode002](https://github.com/hicode002) on repo [qualcomm_gbl_exploit_poc](https://github.com/hicode002/qualcomm_gbl_exploit_poc)

Due to the tools are hardcoded, this could only run on Windows system.

## Setup

When pull this repo to your local dir, run:

```bash
uv sync
```
If you don't have `uv` installed or just don't like it, run:

```bash
pip install -r requirements.txt
```

instead.

It will install the libs that the script needed.

Then run:

```bash
uv run ./main.py
```

or

```bash
python ./main.py
```

to run the script.

## Built-in Commands

- `~bootloader`: try unlocking the bootloader with the bundled EFI file. Only for Snapdragon 8 Elite Gen 5 devices.
- `~ksu [install|uninstall|init]`: manage KernelSU related actions. Currently only `init` is implemented.
- `~selinux [up|down]`: switch SELinux between enforcing (`up`) and permissive (`down`).
- `cls`: clear the console screen.
- `debug`: toggle debug mode for verbose logs.
- `devices`: list connected Android devices.
- `help`: print the built-in help text.
- `pull [SRC_DIR] [LOCAL_TARGET_DIR]`: pull a file or directory from the device into a local target directory.
- `push [LOCAL_SRC_DIR] [TARGET_DIR]`: push a local file or directory into the device target directory.
- `safe`: toggle safe mode. When enabled, dangerous commands such as `rm` are blocked.
- `shell [COMMAND]`: run a command with `adb shell`.
- `switch [SERIAL]`: switch to a specific device by serial number.
- `*[services] *[args]`: run a command through the IMQSNative service.
