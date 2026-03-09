from dataclasses import dataclass
from typing import Optional
import shlex

@dataclass
class Command:
    service: str
    args: str

def parse_command(command_str: str) -> Command:
    """
    解析命令字符串，分离出服务和参数
    
    Args:
        command_str: 命令字符串，格式如 "service_name arg1 arg2" 或 "service_name"
    
    Returns:
        Command对象，包含service和args字段
    
    Examples:
        >>> parse_command("docker run hello-world")
        Command(service='docker', args='run hello-world')
        
        >>> parse_command("python script.py --help")
        Command(service='python', args='script.py --help')
        
        >>> parse_command("ls")
        Command(service='ls', args='')
        
        >>> parse_command('git commit -m "fix bug"')
        Command(service='git', args='commit -m "fix bug"')
    """
    try:
        # 处理空字符串
        if command_str is None:
            return Command(service="", args="")
        
        command_str = str(command_str).strip()
        
        if not command_str:
            return Command(service="", args="")
        
        try:
            parts = shlex.split(command_str)
            if not parts:
                return Command(service="", args="")
            
            service = parts[0]
            
            if len(parts) > 1:
                # 重建参数字符串，保持原始格式
                args_str = ' '.join(parts[1:])
            else:
                args_str = ""
            
            return Command(service=service, args=args_str)
        except (ValueError, OSError) as e:
            parts = command_str.strip().split(maxsplit=1)
    
        if len(parts) == 1:
            return Command(service=parts[0], args="")
        else:
            return Command(service=parts[0], args=parts[1])
            
    except Exception as e:
        # 捕获所有其他异常，返回空命令
        print(f"解析命令时发生错误: {e}")
        return Command(service="", args="")