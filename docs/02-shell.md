# 02 · 外壳汉化（app.asar，1310 条）

## 现状

`app.asar` 里的 `resources/i18n/` 有 40 多种语言，中文是 `zh-Hans.json`。
但官方只写了 **893 / 1310** 条，缺的 **417 条**全是高频按钮和权限弹窗：

```
Cancel / Allow / Allow once / Open / Continue / Save / Install / Remove
Turn on / Sign in to GitHub / Not now / Don't allow / Device tools access …
```

对照 `en-US.json`（1310 条）算差集就能拿到缺失清单。

## 修复流程

```powershell
# 1. 解包 + 合并 + 重打包（普通权限）
python scripts/hanhua.py shell-build --work work

# 2. 提权写回（管理员；会弹 UAC）
python scripts/hanhua.py shell-install --work work --backup backup
```

`shell-build` 干的事：

1. `npx @electron/asar extract <pkg>\resources\app.asar work\shell`
2. 读 `work\shell\resources\i18n\zh-Hans.json`，把 `data/zh_*.json` 里的 417 条并进去
   （**已有键不覆盖**，方便官方以后自己补）
3. `npx @electron/asar pack work\shell work\app-new.asar --unpack "{**/*.node,**/*.exe,**/*.dll}"`
   —— 6 个原生文件必须留在 `app.asar.unpacked`（`.node` / `.dll` / `mcp-server.exe`）

`shell-install` 干的事：

1. 备份 `app.asar` → `backup\app.asar`
2. `takeown` + `icacls` 拿 `app.asar` 和 `claude.exe` 的写权限
3. 覆盖 `app.asar`
4. `node scripts/fuses.js <pkg>\claude.exe disable-asar` —— **关键**
5. 重启 Claude

## 为什么必须关 fuse

Electron 打开 `EnableEmbeddedAsarIntegrityValidation` 后，会在启动时比对你这个 asar 的
分块 SHA256 和 PE 资源里记录的值。一改内容就：

```
FATAL:electron\shell\common\asar\asar_util.cc:357] Integrity check failed for
asar archive entry '<header>' (54cd94… vs fbeec7…, 302117 bytes)
```

进程直接退出，没有窗口。`scripts/fuses.js` 就是把 fuse wire 里那个字节从 `'1'`(49) 改成 `'0'`(48)：

```powershell
node scripts/fuses.js "...\app\claude.exe" show          # 看当前状态
node scripts/fuses.js "...\app\claude.exe" disable-asar  # 关掉
```

注意：这是**改 claude.exe**，MSIX 包签名就对不上了。Windows 不会拦启动，
但应用内"修复/重置"和商店更新会把 exe 换回原版 —— 那时候补丁也就没了，重跑即可。

## 校验

```powershell
# 从安装目录的 asar 里取出语言表，数中文条目
npx @electron/asar extract-file "...\app\resources\app.asar" "resources\i18n\zh-Hans.json"
python -c "import json;d=json.load(open('zh-Hans.json',encoding='utf-8-sig'));print(len(d))"
# 期望 1310
```

或者直接 `python scripts/hanhua.py check`（实测输出）：

```
app.asar: 有  88847759 字节
app.asar 语言表: 1310 条，其中含中文 1284 条      ← 其余 26 条是 Claude/Pro/Max 这类品牌词
fuse: EnableEmbeddedAsarIntegrityValidation: 48   ← 48 = 已关闭
```

## 效果

外壳（侧栏、菜单、弹窗）和 Code 标签页是同一次汉化的结果，效果图见
[README 顶部截图](../assets/code-ui-zh.png)：侧栏「新功能 / 搜索 / 自定义 / 多」、
标题「新会话」、输入框「描述任务或提出问题」都已经是中文。
