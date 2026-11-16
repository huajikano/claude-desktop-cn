# 07 · 踩坑记录（每条都是真报错）

## 1. 安装器静默模式退出码 2

```
PS> & "Claude Desktop Setup.exe" --silent ; $LASTEXITCODE
2
```

`--silent` / `-s` 都不认，日志 `%TEMP%\ClaudeSetup.log` 里根本没有开始的记录。
**解**：别加参数，直接运行，让它自己弹 UAC 和进度条。

## 2. 启动闪退，只在 stderr 里看到 FATAL

```
FATAL:electron\shell\common\asar\asar_util.cc:357] Integrity check failed for
asar archive entry '<header>' (54cd94… vs fbeec7…, 302117 bytes)
```

窗口一帧都不显示。**解**：`node scripts/fuses.js <pkg>\claude.exe disable-asar`。

## 3. 往 WindowsApps 写文件：拒绝访问

```
New-Item: 对路径"C:\Program Files\WindowsApps\Claude_…\app\_writetest.txt"的访问被拒绝。
```

即使当前账号在 Administrators 组，进程是 Medium 完整性级别（`whoami /groups` 看
`Mandatory Label\Medium`）就写不进去。**解**：

```powershell
# 管理员 PowerShell
takeown /f "<文件>" /a
icacls "<文件>" /grant *S-1-5-32-544:(F)
```

## 4. `Start-Process pwsh` 报"系统找不到指定的文件"

这台机器根本没装 PowerShell 7，`pwsh.exe` 不在 PATH。**解**：用
`$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe`，或者直接用当前会话提权。

## 5. 改了 i18n/en-US.json，界面纹丝不动

见 [03-code-ui.md](03-code-ui.md) 事实 2：默认语言不读语言表，读 JS 里的 `defaultMessage`。

## 6. 控制台里中文全是乱码

Windows PowerShell 5.1 默认 GBK 输出，`Get-Content` 看 UTF-8 文件就成"鐨?纭?"这种。
**解**：

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
```

文件本身没坏，用编辑器/read 工具看是正常中文。

## 7. `Out-File -Encoding utf8` 之后再改脚本，中文注释被写成 GBK 乱码

PS 5.1 的 `utf8` 带 BOM，且 `Set-Content` 走过默认编码时会把中文二次编码。
**解**：脚本统一用编辑器/写工具保存为 **UTF-8 无 BOM**，别用 PowerShell 改带中文的脚本。

## 8. Claude Code 报 `tcp connect error 10061`

```
API Error: 502 请求转发失败: 上游请求失败: client error (Connect):
tcp connect error: 由于目标计算机积极拒绝，无法连接。 (os error 10061)
```

`~/.claude/settings.json` 里 `ANTHROPIC_BASE_URL=http://127.0.0.1:15721` 的本地代理没起来。
**解**：先把 CC Switch / 中转站那头跑起来，或改成官方 key 直连。与汉化无关。

## 9. `gh auth login` 用不了的旧 token

`git credential fill` 能取到 `ghp_…`（40 位），但 `GET /user` 返回 401 —— token 过期了。
**解**：`gh auth login --web` 走设备码重新授权（旧凭据不会自动更新）。

## 10. GitHub API 403

`api.github.com/search/...` 未登录时 60 次/小时，搜索接口 10 次/分钟，超限直接 403。
**解**：等一会儿，或者带 token 调；仓库列表也可以用 `releases/latest` 的 302 跳转拿版本号，不占 API 配额。
