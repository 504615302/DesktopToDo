# 桌面代办

Windows 桌面待办卡片：待办、备忘、AI 周报和问答。关闭后进托盘，数据保存在本地。

[下载最新版](https://github.com/504615302/DesktopToDo/releases/latest)

## 下载

打开 [Releases](https://github.com/504615302/DesktopToDo/releases/latest)，按需要选一种：

| 文件 | 用途 |
| --- | --- |
| **DesktopTODO.exe** | 绿色版，下载后双击就能用 |
| **DesktopToDo-Setup.exe** | 安装包，写入开始菜单，可选桌面图标 |

系统要求：Windows 10 / 11 64 位。

### 绿色版

1. 下载 `DesktopTODO.exe`
2. 放到任意文件夹后双击运行
3. 任务和设置写在 exe 同目录的 `data/`、`config/`，方便一起备份

### 安装包

1. 下载并运行 `DesktopToDo-Setup.exe`（不需要管理员权限）
2. 安装到当前用户目录，可勾选创建桌面图标
3. 从开始菜单或桌面打开 **桌面代办**
4. 数据和配置在 `%LOCALAPPDATA%\DesktopToDo\`

卸载：Windows「已安装的应用」里卸载即可。卸载不会删除你的待办数据。

## 开发运行

需要 Python 3.10+。

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 本地打包

```powershell
.\build.ps1
```

生成：

```text
dist\DesktopTODO.exe          绿色版
dist\DesktopToDo-Setup.exe    安装包（需已安装 Inno Setup）
```

打 GitHub Release：把 `v1.1.1` 这类标签推到仓库，Actions 会编译并挂到该 Release 上。

## 使用说明

| 操作 | 方式 |
| --- | --- |
| 新增任务 | 底部输入框回车，或托盘「新增 Todo」 |
| 完成任务 | 点击左侧复选框 |
| 编辑任务 | 双击或右键编辑 |
| 备忘 | 备忘页输入后按 Enter 保存 |
| 问答 | 问答页提问；折叠窗口后只留输入框 |
| 小工具 | 底部「工具」：JSON、翻译、时间戳、编码、哈希、变量别名、老黄历 |
| 置顶 / 主题 / 设置 | 标题栏按钮 |
| 退出 | 托盘菜单「退出」 |

关闭窗口或最小化会隐藏到托盘，不会退出。

## 数据位置

绿色版：

```text
config/settings.json
data/todo.db
```

安装版：

```text
%LOCALAPPDATA%\DesktopToDo\config\settings.json
%LOCALAPPDATA%\DesktopToDo\data\todo.db
```

## 请作者喝咖啡

如果桌面代办帮到你了，欢迎扫码请作者喝杯咖啡。

| 微信 | 支付宝 |
| :---: | :---: |
| <img src="resources/pay/wechat.png" width="260" alt="微信支付"> | <img src="resources/pay/alipay.png" width="260" alt="支付宝"> |
