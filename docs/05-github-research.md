# 05 · GitHub 上还有什么方案（实测对比）

2026-11 调研 + 逐个跑过之后的结果，省得你一个个试错。

## Claude Desktop

| 仓库 | 语言 | 思路 | 对 5.11492.5.0 有效？ | 评价 |
| --- | --- | --- | --- | --- |
| [sheen945/claude-hanhua](https://github.com/sheen945/claude-hanhua) | Go | 44,199 条词库注入 `ion-dist.asar`，处理三层完整性校验 | **词库可用（98.25% 命中）** | exe 只认 Squirrel 版（`%LOCALAPPDATA%\AnthropicClaude\app-*`），不碰 MSIX；但词库质量好，本项目取用其 `zh.json.gz` |
| [good9527/Claude-Desktop-Chinese](https://github.com/good9527/Claude-Desktop-Chinese) | PowerShell | 22,319 条词库覆盖 `en-US.json`，带 10s 自愈守护 | ❌ `install.ps1 -Doctor` 0/100，`Target Type: NOT FOUND` | 它找散文件 `app\resources\ion-dist\i18n\en-US.json`，而 5.11 版本已把 ion-dist 打成 asar；且词典只覆盖我们 44,218 条里的 31.2%，译文机翻味重（`Artifacts`→"制品"） |
| [kael-odin/claude-zh-guard](https://github.com/kael-odin/claude-zh-guard) | TypeScript | MSIX 汉化管理器，自愈 | 未采用 | 太新（2★），思路与 good9527 同类 |
| [GMYXDS/claude-desktop-zh-simple](https://github.com/GMYXDS/claude-desktop-zh-simple) | PowerShell | 只替换 `en-US.json` | ❌ | 已归档，同样假设 i18n 是散文件 |
| [Win-Hao/ClaudeCN](https://github.com/Win-Hao/ClaudeCN) | Rust | macOS 菜单栏小工具 | ❌ | Windows 用不上 |

结论：**词库用 sheen945 的，注入管线自己写**（因为默认语言是 en-US，必须改 JS 字面量，
这一步所有现成项目都没有做，见 [03-code-ui.md](03-code-ui.md)）。

## Claude Code CLI

| 仓库 | 结论 |
| --- | --- |
| [taekchef/claude-code-zh-cn](https://github.com/taekchef/claude-code-zh-cn) | ✅ 直接可用，Windows native `2.1.113–2.1.289` 支持，本机 `2.1.284` 实测通过 |
| Gdenian/claude-code-cn-plus | 同类，未细测 |
| huangguang1999/ccstatusline-zh | 只汉化状态栏插件 |
| jnMetaCode/superpowers-zh | 汉化的是 skills 方法论，不是界面 |
| 1186258278/OpenClawChineseTranslation | 汉化对象是 OpenClaw，不是 Anthropic 的 Claude |

## 顺带一句

`api.github.com` 的仓库搜索很好用（`/search/repositories?q=...`），
但未登录每小时只有 60 次、搜索接口 10 次/分钟，超了直接 403。
