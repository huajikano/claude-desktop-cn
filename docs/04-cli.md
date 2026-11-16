# 04 · Claude Code CLI 汉化

## 现状

从 `2.1.113` 起，npm 主包不再带 `cli.js`，而是原生可执行文件
`%APPDATA%\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe`（246MB，Bun 单文件）。
界面文案全在里面的字节码常量池，Anthropic 没有任何中文资源。

## 为什么不能手工改字符串

字符串表条目是 `[u32 长度|标志][u32 id][UTF-8 内容\0]`，长度字段写死。
中文 UTF-8 每字 3 字节，普遍比英文原文长，**原地替换必然溢出**、破坏后续 id/偏移。

## 社区方案（推荐）

[taekchef/claude-code-zh-cn](https://github.com/taekchef/claude-code-zh-cn)（MIT，849★）：

```powershell
git clone https://github.com/taekchef/claude-code-zh-cn.git
cd claude-code-zh-cn
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
```

它做的事：

1. `settings.json` 注入：`language: Chinese`、187 个中文 spinner 动词、
   41 条中文提示、`SessionStart` / `Notification` / `UserPromptSubmit` 三个 hook
2. 用 `node-lief` 改 PE 结构，把中文按 **UTF-16LE** 写进字节码常量池（绕开长度限制）
3. 启动前自检，失败自动回滚英文；原版留 `claude.exe.zh-cn-backup`

本机实测（`2.1.284`）：

```
native|2.1.284|provisional      ← .patched-version
patched: 1427                   ← claude.exe.zh-cn-repair.json
claude --help → 用法：claude [options] [command] [prompt]
                允许工具访问的额外目录 / 将系统提示追加到默认系统提示
```

会话里 `/zh`（`/chinese`）和 `/en`（`/english`）秒切，不耗 token。
卸载：`powershell -File uninstall.ps1`。

## 另一层：让模型回中文

CLI 界面中文 ≠ 模型回中文。在 `~/.claude/CLAUDE.md` 写死语言规则最稳（对所有项目生效）：

```markdown
- 始终使用简体中文回答。
- 解释、计划、总结、报错说明、代码注释、提交信息全部中文。
- 代码、命令、路径、报错原文保持英文。
```

## 兜底：不用第三方插件也行

只做 Layer 1（改 `settings.json` + `CLAUDE.md`）即可获得「中文回复 + 中文 spinner」，
界面本身仍是英文 —— 但 CLI 永远不会因为补丁坏掉。
