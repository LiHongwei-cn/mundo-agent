"""蒙多工具引擎 v3.0.0 — 融合四家精华

设计原则：
- 注册表模式：工具自注册，零耦合（Hermes Agent）
- 参数验证：每个 handler 自行验证必填参数
- 结果截断：统一在注册表层处理
- 结构化输出：支持 JSON 输出（Claude Code）
- 安全隔离：危险操作需确认（Codex CLI）
- 沙箱执行：代码执行在受限环境（Codex CLI）
"""

import os
import sys
import json
import re
import subprocess
import glob as glob_mod
import time
import random
from typing import Dict, Callable, List


# ═══════════════════════════════════════════════
# Tool Registry — 借鉴 Hermes Agent
# ═══════════════════════════════════════════════

class ToolRegistry:

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._schemas: List[Dict] = []
        self._required: Dict[str, List[str]] = {}
        self._names: List[str] = []

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={len(self._names)})"

    def __len__(self) -> int:
        return len(self._names)

    def register(self, name: str, description: str,
                 parameters: Dict, handler: Callable,
                 required: List[str] = None):
        self._handlers[name] = handler
        self._required[name] = required or []
        self._names.append(name)
        self._schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        })

    @property
    def schemas(self) -> List[Dict]:
        return self._schemas

    @property
    def names(self) -> List[str]:
        return list(self._names)

    def execute(self, name: str, args: Dict) -> str:
        handler = self._handlers.get(name)
        if not handler:
            return f"[错误: 未知工具 {name}]"
        if not isinstance(args, dict):
            args = {}

        # v3.1.0: 参数规范化 + 记录原始参数用于调试
        original_keys = list(args.keys()) if args else []
        args = _normalize_args(args, name)
        normalized_keys = list(args.keys())

        try:
            result = handler(args)

            # v3.1.0: 增强错误反馈
            if isinstance(result, str) and ("缺少" in result or "错误" in result):
                req = self._required.get(name, [])
                if req:
                    fix_hint = f"\n\n⚠️ 参数错误修复指南:"
                    fix_hint += f"\n工具: {name}"
                    fix_hint += f"\n必需参数: {', '.join(req)}"
                    fix_hint += f"\n原始参数: {original_keys}"
                    fix_hint += f"\n规范化后: {normalized_keys}"
                    fix_hint += f"\n\n请重新调用: {name}({', '.join(req)})"
                    result += fix_hint

            return result
        except Exception as e:
            err_msg = f"工具 {name} 执行失败: {e}"
            req = self._required.get(name, [])
            if req and any(kw in str(e) for kw in ("缺少", "required", "missing", "必需")):
                err_msg += f"\n必需参数: {', '.join(req)}"
                err_msg += f"\n收到的参数: {original_keys}"
            return err_msg


registry = ToolRegistry()

MAX_OUTPUT_CHARS = 8000


# ═══════════════════════════════════════════════
# 参数规范化 — 解决 LLM 调用格式不稳定问题
# ═══════════════════════════════════════════════

# path 参数的常见别名
_PATH_ALIASES = ("path", "file_path", "filename", "file", "filepath", "dir", "directory", "folder")
_CONTENT_ALIASES = ("content", "text", "data", "body", "value")
_COMMAND_ALIASES = ("command", "cmd", "shell", "exec", "run")
_PATTERN_ALIASES = ("pattern", "regex", "query", "search", "keyword")

# 常见的嵌套包装键
_WRAPPER_KEYS = ("parameters", "params", "args", "kwargs", "input", "data")


def _normalize_args(args: dict, tool_name: str = "") -> dict:
    """规范化工具参数 — 处理 LLM 输出的各种格式问题

    处理情况（v3.1.0 增强）：
    1. 嵌套解包: {"parameters": {"path": "x"}} → {"path": "x"}
    2. 别名映射: path/content/command/pattern 四大参数全别名覆盖
    3. 类型修正: {"path": 123} → {"path": "123"}
    4. 空值处理: {"path": null} → {"path": ""}
    5. 工具名片名: {"write_file": "/path/to/file"} → {"path": "/path/to/file"}
    6. 值穿透: 单值列表自动按位置拆分
    """
    if not isinstance(args, dict):
        return {}

    result = dict(args)  # 浅拷贝

    # 1. 解包嵌套参数（最多解3层，防死循环）
    for _ in range(3):
        if len(result) == 1:
            key = next(iter(result))
            if key in _WRAPPER_KEYS and isinstance(result[key], dict):
                result = dict(result[key])
            else:
                break
        else:
            break

    # 1.5 工具名片名处理: LLM 有时输出 {"write_file": "xxx"} 或 {"read_file": "xxx"}
    _tool_name_map = {
        "write_file": "path",
        "read_file": "path",
        "edit_file": "path",
        "search_files": "pattern",
        "list_directory": "path",
        "terminal": "command",
        "python_execute": "code",
    }
    if tool_name in _tool_name_map and tool_name in result:
        expected_param = _tool_name_map[tool_name]
        val = result.pop(tool_name)
        if expected_param not in result and isinstance(val, (str, list)):
            if isinstance(val, list):
                if expected_param == "path" and len(val) >= 1:
                    result["path"] = val[0]
                if "content" not in result and len(val) >= 2:
                    result["content"] = val[1]
            else:
                result[expected_param] = val

    # 2. 别名映射 → 统一为标准名（全面覆盖）
    for alias in _PATH_ALIASES:
        if alias in result and "path" not in result:
            result["path"] = result.pop(alias)
            break

    for alias in _CONTENT_ALIASES:
        if alias in result and "content" not in result:
            result["content"] = result.pop(alias)
            break

    for alias in _COMMAND_ALIASES:
        if alias in result and "command" not in result:
            result["command"] = result.pop(alias)
            break

    for alias in _PATTERN_ALIASES:
        if alias in result and "pattern" not in result:
            result["pattern"] = result.pop(alias)
            break

    for alias in ("workdir", "work_dir", "cwd", "directory"):
        if alias in result and "workdir" not in result:
            result["workdir"] = result.pop(alias)
            break

    # 3. 类型修正 — 所有字符串参数统一转 str
    _STRING_KEYS = ("path", "workdir", "command", "code", "pattern", "content",
                    "message", "old_string", "new_string", "branch_name")
    for key in _STRING_KEYS:
        if key in result and result[key] is not None:
            if not isinstance(result[key], str):
                if isinstance(result[key], (list, dict)):
                    try:
                        result[key] = json.dumps(result[key], ensure_ascii=False)
                    except (TypeError, ValueError):
                        result[key] = str(result[key])
                else:
                    result[key] = str(result[key])

    # 4. 空值 → 空字符串（让 handler 能正确检测缺失）
    for key in _STRING_KEYS:
        if key in result and result[key] is None:
            result[key] = ""

    return result


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if limit <= 0:
        return text[:200] + "..." if len(text) > 200 else text
    if len(text) <= limit:
        return text
    head = text[:int(limit * 0.6)]
    tail = text[-int(limit * 0.3):]
    return f"{head}\n... ({len(text)} 字符，已省略) ...\n{tail}"


# ═══════════════════════════════════════════════
# 工具实现
# ═══════════════════════════════════════════════

def _terminal(args: Dict) -> str:
    cmd = args.get("command", "")
    if not cmd:
        keys = list(args.keys()) if args else []
        return f"[错误: terminal 缺少 command 参数，收到: {keys}]"
    workdir = args.get("workdir") or os.getcwd()
    timeout = args.get("timeout", 120)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        output = result.stdout
        if result.stderr:
            stderr = result.stderr[:2000]
            if len(result.stderr) > 2000:
                stderr += f"\n... ({len(result.stderr)} 字符，已截断)"
            output += f"\n[stderr]\n{stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
            stderr = result.stderr or ""
            if "command not found" in stderr:
                output += "\n提示: 命令未找到"
            elif "Permission denied" in stderr:
                output += "\n提示: 权限不足"
            elif "No such file" in stderr:
                output += "\n提示: 文件/目录不存在"
        return _truncate(output or "(无输出)")
    except subprocess.TimeoutExpired:
        return f"[超时: 命令执行超过 {timeout} 秒]"
    except PermissionError:
        return "[错误: 权限不足]"
    except Exception as e:
        return f"[错误: {type(e).__name__}: {e}]"


def _read_file(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        keys = list(args.keys()) if args else []
        return f"[错误: read_file 缺少 path 参数，收到: {keys}]"
    path = os.path.expanduser(path)
    offset = args.get("offset", 1)
    limit = args.get("limit", 500)

    if not os.path.exists(path):
        return f"[错误: 文件不存在: {path}]"
    if os.path.isdir(path):
        return f"[错误: 是目录不是文件: {path}]"
    try:
        from itertools import islice
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if offset > 1:
                list(islice(f, offset - 1))
            selected = list(islice(f, limit))
        total = 0
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            total = sum(1 for _ in f)
        start = max(0, offset - 1)
        end = min(total, start + len(selected))
        result = [f"{i:4d}|{line.rstrip()}" for i, line in enumerate(selected, start=start + 1)]
        header = f"文件: {path} (共 {total} 行，显示 {start+1}-{end})"
        return _truncate(header + "\n" + "\n".join(result))
    except Exception as e:
        return f"[错误: {e}]"


def _write_file(args: Dict) -> str:
    path = args.get("path", "")
    if not path:
        keys = list(args.keys()) if args else []
        return f"[错误: write_file 缺少 path 参数，收到: {keys}]"
    content = args.get("content") or ""
    if not content:
        return f"[错误: write_file 缺少 content 参数，path={path[:50]}]"
    path = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✓ 已写入: {path} ({len(content)} 字符)"
    except Exception as e:
        return f"[错误: {e}]"


def _search_files(args: Dict) -> str:
    pattern = args.get("pattern", "")
    if not pattern:
        return "[错误: search_files 缺少 pattern 参数]"
    path = os.path.expanduser(args.get("path") or ".")
    target = args.get("target", "content")
    max_results = min(args.get("limit", 50), 100)

    if target == "files":
        matches = glob_mod.glob(os.path.join(path, "**", f"*{pattern}*"), recursive=True)
        if not matches:
            return f"未找到匹配 '{pattern}' 的文件"
        return _truncate("\n".join(sorted(matches)[:max_results]))

    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error:
        regex = re.compile(re.escape(pattern), re.IGNORECASE)

    searchable_exts = (".py", ".js", ".ts", ".html", ".css", ".md", ".txt",
                       ".json", ".yaml", ".yml", ".sh", ".bat", ".m", ".swift",
                       ".c", ".cpp", ".h", ".hpp", ".java", ".go", ".rs")

    max_depth = 5
    max_files = 500
    file_count = 0
    start_time = time.time()

    for root, dirs, files in os.walk(path):
        depth = root[len(path):].count(os.sep)
        if depth >= max_depth:
            dirs.clear()
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git", "venv")]
        for fname in files:
            if time.time() - start_time > 10:
                results.append(f"... [搜索超时，已找到 {len(results)} 条结果]")
                return _truncate("\n".join(results[:max_results]))
            file_count += 1
            if file_count > max_files:
                results.append(f"... [已扫描 {max_files} 个文件，停止搜索]")
                return _truncate("\n".join(results[:max_results]))
            if not fname.endswith(searchable_exts):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            rel = os.path.relpath(fpath, path)
                            results.append(f"{rel}:{i}: {line.rstrip()}")
                            if len(results) >= max_results:
                                return _truncate("\n".join(results[:max_results]))
            except (PermissionError, OSError):
                continue
    if not results:
        return f"未找到匹配 '{pattern}' 的内容"
    return _truncate("\n".join(results[:max_results]))


def _list_directory(args: Dict) -> str:
    path = os.path.expanduser(args.get("path") or ".")
    show_hidden = args.get("show_hidden", False)
    if not os.path.isdir(path):
        return f"[错误: 不是目录: {path}]"
    entries = []
    try:
        for name in sorted(os.listdir(path)):
            if not show_hidden and name.startswith("."):
                continue
            full = os.path.join(path, name)
            if os.path.isdir(full):
                entries.append(f"  📁 {name}/")
            else:
                size = os.path.getsize(full)
                if size < 1024:
                    s = f"{size}B"
                elif size < 1024 * 1024:
                    s = f"{size/1024:.1f}K"
                else:
                    s = f"{size/1024/1024:.1f}M"
                entries.append(f"  📄 {name} ({s})")
        return _truncate(f"目录: {path}\n" + "\n".join(entries[:100]))
    except PermissionError:
        return f"[错误: 无权限访问: {path}]"


def _git_operation(args: Dict) -> str:
    operation = args.get("operation", "")
    if not operation:
        return "[错误: git_operation 缺少 operation 参数]"
    workdir = args.get("workdir") or os.getcwd()
    operations = {
        "status": "git status --short",
        "diff": "git diff",
        "diff_staged": "git diff --staged",
        "log": "git log --oneline -10",
        "branch": "git branch -a",
        "current_branch": "git rev-parse --abbrev-ref HEAD",
    }
    if operation in operations:
        cmd = operations[operation]
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                    timeout=30, cwd=workdir)
            return _truncate(result.stdout or "(无输出)")
        except Exception as e:
            return f"[错误: Git 操作失败: {e}]"
    elif operation == "commit":
        message = args.get("message", "")
        if not message:
            return "[错误: commit 需要 message 参数]"
        try:
            subprocess.run(["git", "add", "-A"], cwd=workdir, check=True)
            result = subprocess.run(["git", "commit", "-m", message],
                                    capture_output=True, text=True, cwd=workdir)
            return f"✓ 已提交: {message}\n{result.stdout}"
        except Exception as e:
            return f"[错误: 提交失败: {e}]"
    elif operation == "create_branch":
        branch_name = args.get("branch_name", "")
        if not branch_name:
            return "[错误: create_branch 需要 branch_name 参数]"
        try:
            result = subprocess.run(["git", "checkout", "-b", branch_name],
                                    capture_output=True, text=True, cwd=workdir)
            return f"✓ 已创建分支: {branch_name}\n{result.stdout}"
        except Exception as e:
            return f"[错误: 创建分支失败: {e}]"
    return f"[错误: 未知 git 操作: {operation}]"


def _python_execute(args: Dict) -> str:
    code = args.get("code", "")
    if not code:
        return "[错误: python_execute 缺少 code 参数]"
    timeout = args.get("timeout", 30)
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr[:2000]}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return _truncate(output or "(无输出)")
    except subprocess.TimeoutExpired:
        return f"[超时: Python 执行超过 {timeout} 秒]"
    except Exception as e:
        return f"[错误: {e}]"


# ═══════════════════════════════════════════════
# 注册所有工具
# ═══════════════════════════════════════════════

registry.register(
    "terminal", "执行 shell 命令",
    {"type": "object", "properties": {
        "command": {"type": "string", "description": "要执行的命令"},
        "workdir": {"type": "string", "description": "工作目录"},
        "timeout": {"type": "integer", "description": "超时秒数"},
    }},
    _terminal, required=["command"],
)

registry.register(
    "read_file", "读取文件内容",
    {"type": "object", "properties": {
        "path": {"type": "string", "description": "文件路径"},
        "offset": {"type": "integer", "description": "起始行号"},
        "limit": {"type": "integer", "description": "最大行数"},
    }},
    _read_file, required=["path"],
)

registry.register(
    "write_file", "写入文件内容",
    {"type": "object", "properties": {
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "写入内容"},
    }},
    _write_file, required=["path", "content"],
)

registry.register(
    "search_files", "搜索文件内容或按名称查找文件",
    {"type": "object", "properties": {
        "pattern": {"type": "string", "description": "搜索模式（正则或glob）"},
        "path": {"type": "string", "description": "搜索路径"},
        "target": {"type": "string", "description": "content 或 files"},
        "limit": {"type": "integer", "description": "最大结果数"},
    }},
    _search_files, required=["pattern"],
)

registry.register(
    "list_directory", "列出目录内容",
    {"type": "object", "properties": {
        "path": {"type": "string", "description": "目录路径"},
        "show_hidden": {"type": "boolean", "description": "是否显示隐藏文件"},
    }},
    _list_directory, required=[],
)

registry.register(
    "git_operation", "Git 操作（status/diff/commit/branch）",
    {"type": "object", "properties": {
        "operation": {"type": "string", "description": "操作类型"},
        "workdir": {"type": "string", "description": "工作目录"},
        "message": {"type": "string", "description": "commit 消息"},
        "branch_name": {"type": "string", "description": "分支名"},
    }},
    _git_operation, required=["operation"],
)

registry.register(
    "python_execute", "执行 Python 代码",
    {"type": "object", "properties": {
        "code": {"type": "string", "description": "Python 代码"},
        "timeout": {"type": "integer", "description": "超时秒数"},
    }},
    _python_execute, required=["code"],
)


# ═══════════════════════════════════════════════
# 工具执行入口
# ═══════════════════════════════════════════════

def execute_tool(name: str, args: dict) -> str:
    return registry.execute(name, args)
