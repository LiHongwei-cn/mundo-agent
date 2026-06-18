#!/bin/bash
# MUNDO Agent v2.2.7 — macOS 双击启动器
# 每次启动强制同步，确保运行最新版

SRC="$HOME/Desktop/lihongwei-cn/mundo-agent"
DST="$HOME/.hermes/mundo-agent"

mkdir -p "$DST"

# 源存在时强制同步
if [ -d "$SRC" ] && [ -f "$SRC/version.txt" ] && [ -f "$SRC/mundo.py" ]; then
    # 同步所有 .py 文件（增量）
    for f in "$SRC"/*.py; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        if ! diff -q "$f" "$DST/$base" >/dev/null 2>&1; then
            cp "$f" "$DST/$base"
        fi
    done

    # 同步核心文件
    for f in version.txt requirements.txt pytest.ini Dockerfile docker-compose.yml README.md; do
        [ -f "$SRC/$f" ] || continue
        if ! diff -q "$SRC/$f" "$DST/$f" >/dev/null 2>&1; then
            cp "$SRC/$f" "$DST/$f"
        fi
    done

    # 同步目录
    for dir in mundo_agent tests config docs examples skill_store .github; do
        if [ -d "$SRC/$dir" ]; then
            rsync -a --delete --exclude='__pycache__' "$SRC/$dir/" "$DST/$dir/"
        fi
    done
fi

# 确保 setup_complete 存在
if [ ! -f "$DST/.setup_complete" ] && [ -f "$DST/.env" ]; then
    if grep -q "API_KEY" "$DST/.env" 2>/dev/null; then
        echo "xiaomi
mimo-v2.5-pro" > "$DST/.setup_complete"
    fi
fi

cd "$DST"
export PYTHONDONTWRITEBYTECODE=1
exec python3 mundo.py "$@"
