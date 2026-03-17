from dataclasses import dataclass, field
from typing import List
import os
import shlex


@dataclass
class Command:
    service: str
    args: str
    argv: List[str] = field(default_factory=list)


def parse_argv(args_str: str) -> List[str]:
    if not args_str:
        return []

    try:
        parts = shlex.split(args_str, posix=os.name != "nt")
    except (ValueError, OSError):
        return args_str.split()

    normalized_parts = []
    for part in parts:
        if len(part) >= 2 and part[0] == part[-1] and part[0] in {"'", '"'}:
            normalized_parts.append(part[1:-1])
        else:
            normalized_parts.append(part)

    return normalized_parts


def parse_command(command_str: str) -> Command:
    """
    Parse user input into a command name and argument list.

    `args` keeps the original argument substring so existing shell-style
    commands continue to behave as before, while `argv` provides tokenized
    arguments for commands that need structured path parsing.
    """
    try:
        if command_str is None:
            return Command(service="", args="", argv=[])

        command_str = str(command_str).strip()
        if not command_str:
            return Command(service="", args="", argv=[])

        parts = command_str.split(maxsplit=1)
        if not parts:
            return Command(service="", args="", argv=[])

        service = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        argv = parse_argv(args)
        return Command(service=service, args=args, argv=argv)

    except Exception as e:
        print(f"Parse command failed: {e}")
        return Command(service="", args="", argv=[])
