#!/bin/bash
# MUNDO Agent v2.2.7 — macOS 双击启动器
# 同步逻辑静默执行，Terminal 只显示蒙多

SRC="$HOME/Desktop/lihongwei-cn/mundo-agent"
DST="$HOME/.hermes/mundo-agent"

# 确保目标目录存在
mkdir -p "$DST"

# 同步版本文件（如果源存在）
if [ -f "$SRC/version.txt" ] && [ -f "$DST/version.txt" ]; then
    SRC_VER=$(cat "$SRC/version.txt" | tr -d '[:space:]')
    DST_VER=$(cat "$DST/version.txt" | tr -d '[:space:]')

    if [ "$SRC_VER" != "$DST_VER" ]; then
        echo "  版本不同步: $DST_VER → $SRC_VER，正在同步..."

        # 同步所有 .py 文件
        for f in "$SRC"/*.py; do
            [ -f "$f" ] && cp "$f" "$DST/$(basename "$f")"
        done

        # 同步核心配置文件
        for f in version.txt requirements.txt pytest.ini Dockerfile docker-compose.yml README.md; do
            [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DST/$f"
        done

        # 同步目录
        for dir in mundo_agent tests config docs examples skill_store .github; do
            if [ -d "$SRC/$dir" ]; then
                rsync -a --delete --exclude='__pycache__' "$SRC/$dir/" "$DST/$dir/"
            fi
        done

        echo "  同步完成！"
    fi
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
