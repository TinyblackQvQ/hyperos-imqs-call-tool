> README in [English](../README.md)

## HyperOS IMQSNative Service Call Tool

该工具可以让用户以System权限运行任何命令并获取其执行结果；

具体的实现原理是通过MIUI时期遗留的老产物miui.mqsas.IMQSNative中的漏洞进行提权运行命令。

只要在selinux宽容的状态下即可运行任意指令：

```bash
service call miui.mqsas.IMQSNative 21 i32 1 s16 "[COMMAND]" i32 1 s16 "[PARAMETERS]" s16 "[LOGPATH]" i32 60
```

设置selinux宽容则是通过fastboot的gpu-preemption-value设定为0后的属性将默认设置，通过类SQL的注入攻击进行设置：

```bash
fastboot oem set-gpu-preemption-value 0 androidboot.selinux=permissive
```

再结合骁龙 8 Elite Gen 5 芯片新增的efsip分区，由于没有进行校验的同时又会在系统启动时执行，可以直接通过系统写入该分区特定的解锁文件来强硬设置设备Bootloader锁为解锁状态。

该efi解锁文件由[@hicode002](https://github.com/hicode002)编写和编译，发布在仓库[qualcomm_gbl_exploit_poc](https://github.com/hicode002/qualcomm_gbl_exploit_poc)中。

这个Bug在2026年2月安全补丁中被修复，一般系统版本高于等于 3.0.6 (对老机型如 Xiaomi 13 & Redmi K70) ~ 3.0.22 (对新机型如 Xiaomi 17 & Redmi K90 Pro Max)有概率不可用。

由于仓库携带的`Flashtool`是`exe`可执行程序，且脚本中`cls`命令直接使用`os.system("cls")`，该工具只能在Windows上运行。

**数据无价！在运行任意命令时三思而后行！本工具不对你的设备负任何责任！产生的任意损失概不负责！**

## 安装

将本仓库整体拉至本地文件夹，然后运行：

```bash
uv sync
```
如果你没有使用`uv`的话，也可以运行：

```bash
pip install -r requirements.txt
```

来安装依赖库。

之后运行：

```bash
uv run ./main.py
```

或者

```bash
python ./main.py
```

来运行脚本。

## 功能

- `~bootloader`: 尝试使用仓库附带的 EFI 文件解锁 Bootloader。仅限骁龙 8 Elite Gen 5 机型使用。
- `~ksu [install|uninstall|init]`: 管理 KernelSU 相关动作。目前仅 `init` 已实现。
- `~selinux [up|down]`: 切换 SELinux 状态，`up` 为强制模式，`down` 为宽容模式。
- `cls`: 清除控制台内容。
- `debug`: 切换工具调试模式，为 `True` 时显示更详细的运行日志。
- `devices`: 获取已连接设备的信息。
- `help`: 显示内置帮助信息。
- `pull [SRC_DIR] [LOCAL_TARGET_DIR]`: 从设备拉取文件或目录到本地目标目录。
- `push [LOCAL_SRC_DIR] [TARGET_DIR]`: 将本地文件或目录推送到设备目标目录。
- `safe`: 切换工具安全模式，为 `True` 时禁止一些危险操作，例如 `rm`。
- `shell [COMMAND]`: 使用 `adb shell` 运行命令。
- `switch [SERIAL]`: 按序列号切换到指定设备。
- `*[services] *[args]`: 使用 IMQSNative 服务运行命令。

## 许可

MIT
