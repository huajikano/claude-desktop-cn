#!/usr/bin/env python3
"""Claude 桌面版汉化工具箱（Windows / MSIX + Squirrel 通用）。

子命令：
  check          体检：列出安装目录、asar 状态、中文占比
  shell-build    解包 app.asar → 合并中文词条 → 重新打包
  shell-install  提权写回 app.asar，并关闭 asar 完整性 fuse（需要管理员）
  ion-build      解包 ion-dist.asar → 替换 JS 里的 defaultMessage → 重新打包
  ion-install    提权写回 ion-dist.asar（需要管理员）
  restore        从备份还原官方原版

依赖：
  - Node.js（脚本内部用 npx 调 @electron/asar、@electron/fuses）
  - Python 3.8+
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CJK = re.compile(r"[\u4e00-\u9fff]")


# ---------------------------------------------------------------- 基础工具
def run(cmd, **kw):
    print("  $ " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, check=True, **kw)


def asar(*args):
    """调用 @electron/asar（npx 自动拉取/复用缓存）。"""
    run(["npx", "--yes", "@electron/asar@3", *args], shell=True)


def find_package(explicit=None):
    """找到 Claude 的 app 目录（MSIX 在 WindowsApps，Squirrel 在 LocalAppData）。"""
    if explicit:
        p = Path(explicit)
        return p if p.name != "app" else p
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-AppxPackage -Name '*Claude*' | Sort-Object Version -Descending | "
             "Select-Object -First 1).InstallLocation"],
            capture_output=True, text=True, timeout=120).stdout.strip()
        if out:
            cand = Path(out) / "app"
            if (cand / "resources" / "app.asar").exists():
                return cand
    except Exception:
        pass
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "AnthropicClaude"
    if base.exists():
        for d in sorted(base.glob("app-*"), reverse=True):
            if (d / "resources" / "app.asar").exists():
                return d
    raise SystemExit("找不到 Claude 安装目录，请用 --pkg 指定（形如 ...\\app 或 ...\\app-1.2.3）")


def need_admin():
    if os.name != "nt":
        return
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise SystemExit("这个操作要管理员权限：右键 PowerShell → 以管理员身份运行，再跑一次")


def takeown(path):
    run(["takeown", "/f", str(path), "/a"], shell=True)
    run(["icacls", str(path), "/grant", "*S-1-5-32-544:(F)"], shell=True)


def count_cjk(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return None, None
    total = len(data)
    zh = sum(1 for v in data.values() if isinstance(v, str) and CJK.search(v))
    return total, zh


# ---------------------------------------------------------------- check
def cmd_check(args):
    pkg = find_package(args.pkg)
    res = pkg / "resources"
    print(f"安装目录: {pkg}")
    for name in ("app.asar", "ion-dist.asar"):
        f = res / name
        print(f"  {name}: {'有' if f.exists() else '无'}  {f.stat().st_size if f.exists() else 0} 字节")
    exe = pkg / "claude.exe"
    if exe.exists():
        fuse = subprocess.run(["node", str(Path(__file__).with_name("fuses.js")), str(exe), "show"],
                              capture_output=True, text=True)
        print("  " + fuse.stdout.strip().replace("\n", "\n  "))

    cwd = Path.cwd()
    for asar_name, member in (("app.asar", r"resources\i18n\zh-Hans.json"),
                              ("ion-dist.asar", r"i18n\en-US.json")):
        f = res / asar_name
        if not f.exists():
            continue
        got = False
        for m in (member, member.replace("\\", "/")):
            try:
                subprocess.run(["npx", "--yes", "@electron/asar@3", "extract-file", str(f), m],
                               shell=True, check=True, capture_output=True)
            except Exception as exc:
                continue
            base = re.split(r"[\\/]", m)[-1]
            extracted = cwd / base
            if extracted.exists():
                total, zh = count_cjk(extracted)
                if total:
                    print(f"  {asar_name} 语言表: {total} 条，其中含中文 {zh} 条")
                extracted.unlink(missing_ok=True)
            got = True
            break
        if not got:
            print(f"  {asar_name}: 语言表读取失败（结构可能变了）")


# ---------------------------------------------------------------- shell
def cmd_shell_build(args):
    pkg = find_package(args.pkg)
    work = Path(args.work)
    src = work / "shell"
    if src.exists():
        shutil.rmtree(src)
    src.parent.mkdir(parents=True, exist_ok=True)
    print("[1/4] 解包 app.asar")
    asar("extract", str(pkg / "resources" / "app.asar"), str(src))

    print("[2/4] 合并中文词条")
    catalog_path = src / "resources" / "i18n" / "zh-Hans.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    before = len(catalog)
    extra = {}
    for f in sorted(Path(args.extra).glob("*.json")):
        extra.update(json.loads(f.read_text(encoding="utf-8")))
    for k, v in extra.items():
        catalog.setdefault(k, v)
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print(f"  官方 {before} 条 + 增补 {len(extra)} 条 → {len(catalog)} 条")

    print("[3/4] 重新打包")
    out = work / "app-new.asar"
    out.unlink(missing_ok=True)
    asar("pack", str(src), str(out), "--unpack", "{**/*.node,**/*.exe,**/*.dll}")
    print(f"[4/4] 完成: {out} ({out.stat().st_size} 字节)")
    print("下一步（管理员）：python hanhua.py shell-install")


def cmd_shell_install(args):
    need_admin()
    pkg = find_package(args.pkg)
    res = pkg / "resources"
    new = Path(args.work) / "app-new.asar"
    if not new.exists():
        raise SystemExit(f"先跑 shell-build，找不到 {new}")

    backup = Path(args.backup or "backup") / "app.asar"
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(res / "app.asar", backup)
        print(f"已备份原版 → {backup}")

    for name in ("app.asar", "claude.exe"):
        target = res / name if name.endswith(".asar") else pkg / name
        if target.exists():
            print(f"取得写权限: {target}")
            takeown(target)

    print("写回 app.asar")
    shutil.copy2(new, res / "app.asar")

    print("关闭 asar 完整性 fuse")
    run(["node", str(Path(__file__).with_name("fuses.js")), str(pkg / "claude.exe"), "disable-asar"])
    print("完成，重启 Claude 即可")


# ---------------------------------------------------------------- ion
def cmd_ion_build(args):
    pkg = find_package(args.pkg)
    work = Path(args.work)
    src = work / "ion"
    if src.exists():
        shutil.rmtree(src)
    src.parent.mkdir(parents=True, exist_ok=True)
    print("[1/4] 解包 ion-dist.asar")
    asar("extract", str(pkg / "resources" / "ion-dist.asar"), str(src))

    index = src / "i18n" / "en-US.json"
    if not index.exists():
        raise SystemExit("ion-dist 里没有 i18n/en-US.json，版本结构可能变了")
    en_cat = json.loads(index.read_text(encoding="utf-8-sig"))

    dict_path = Path(args.dict)
    if not dict_path.exists():
        raise SystemExit(f"找不到词库 {dict_path}（见 README：从 claude-hanhua 下 zh.json.gz）")
    import gzip
    try:
        zh_cat = json.loads(gzip.open(dict_path, "rt", encoding="utf-8").read())
    except OSError:
        zh_cat = json.loads(dict_path.read_text(encoding="utf-8"))

    en2zh = {}
    for k, en in en_cat.items():
        zv = zh_cat.get(k)
        if zv and zv != en and CJK.search(zv):
            en2zh.setdefault(en, zv)
    print(f"[2/4] 词库 {len(zh_cat)} 条，可映射英文短语 {len(en2zh)} 个")

    print("[3/4] 替换 JS 里的 defaultMessage")
    STR = r'"((?:[^"\\\n]|\\.)*)"'
    pat = re.compile(r"defaultMessage:" + STR)
    esc = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
    total = 0
    files = 0

    def to_lit(s):
        return '"' + "".join(esc.get(c, c) for c in s) + '"'

    for js in src.rglob("*.js"):
        try:
            text = js.read_bytes().decode("utf-8", "surrogatepass")
        except Exception:
            continue
        box = {"n": 0}

        def repl(m):
            eng = m.group(1)
            if "\\" in eng:
                try:
                    eng = eng.encode().decode("unicode_escape")
                except Exception:
                    return m.group(0)
            zh = en2zh.get(eng)
            if not zh:
                return m.group(0)
            box["n"] += 1
            return "defaultMessage:" + to_lit(zh)

        new = pat.sub(repl, text)
        if box["n"]:
            js.write_bytes(new.encode("utf-8", "surrogatepass"))
            total += box["n"]
            files += 1
    print(f"  替换 {total} 处，改动 {files} 个 js 文件")

    out = work / "ion-dist.new.asar"
    out.unlink(missing_ok=True)
    asar("pack", str(src), str(out))
    print(f"[4/4] 完成: {out} ({out.stat().st_size} 字节)")
    print("下一步（管理员）：python hanhua.py ion-install")


def cmd_ion_install(args):
    need_admin()
    pkg = find_package(args.pkg)
    new = Path(args.work) / "ion-dist.new.asar"
    if not new.exists():
        raise SystemExit(f"先跑 ion-build，找不到 {new}")
    target = pkg / "resources" / "ion-dist.asar"
    backup = Path(args.backup or "backup") / "ion-dist.asar"
    if not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        print("备份原版（200MB 左右，稍等）…")
        shutil.copy2(target, backup)
    takeown(target)
    shutil.copy2(new, target)
    print("完成，重启 Claude 即可")


# ---------------------------------------------------------------- restore
def cmd_restore(args):
    need_admin()
    pkg = find_package(args.pkg)
    res = pkg / "resources"
    bak = Path(args.backup or "backup")
    pairs = [(bak / "app.asar", res / "app.asar"),
             (bak / "ion-dist.asar", res / "ion-dist.asar"),
             (bak / "claude.exe", pkg / "claude.exe")]
    done = 0
    for src, dst in pairs:
        if src.exists():
            takeown(dst)
            shutil.copy2(src, dst)
            print(f"还原 {dst.name}")
            done += 1
    if not done:
        raise SystemExit(f"{bak} 里没有备份")
    print("完成，重启 Claude 即可")


def main():
    ap = argparse.ArgumentParser(description="Claude 桌面版汉化工具箱")
    ap.add_argument("--pkg", help="Claude 安装目录（默认自动探测 MSIX / Squirrel）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="体检").set_defaults(func=cmd_check)

    p = sub.add_parser("shell-build", help="构建中文 app.asar")
    p.add_argument("--work", default="work")
    p.add_argument("--extra", default="data", help="增补词条目录（*.json）")
    p.set_defaults(func=cmd_shell_build)

    p = sub.add_parser("shell-install", help="写回 app.asar（管理员）")
    p.add_argument("--work", default="work")
    p.add_argument("--backup", default="backup")
    p.set_defaults(func=cmd_shell_install)

    p = sub.add_parser("ion-build", help="构建中文 ion-dist.asar")
    p.add_argument("--work", default="work")
    p.add_argument("--dict", default="dict/zh.json.gz", help="claude-hanhua 的 zh.json.gz")
    p.set_defaults(func=cmd_ion_build)

    p = sub.add_parser("ion-install", help="写回 ion-dist.asar（管理员）")
    p.add_argument("--work", default="work")
    p.add_argument("--backup", default="backup")
    p.set_defaults(func=cmd_ion_install)

    p = sub.add_parser("restore", help="还原官方原版（管理员）")
    p.add_argument("--backup", default="backup")
    p.set_defaults(func=cmd_restore)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
