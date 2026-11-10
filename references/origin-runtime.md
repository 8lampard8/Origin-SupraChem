# Windows / Origin 运行方式

## 已验证的路径

- 外部 Python + `win32com.client.DispatchEx('Origin.Application')` 启动独立实例，`Visible=100`，`Load(完整路径)`，`Execute('run -pyf "...";')` 运行 Origin 自带 Python。
- `Dispatch('Origin.ApplicationSI')` 可连接已有实例，但多实例时目标可能不确定。不要对未经核实的活动项目执行修改。`GetActiveObject` 未注册并不说明 Origin 不存在。
- 外部 COM 没有已验证的 `GetLTStr` 方法；在内置 Python 用 `op.get_lt_str('%G')`、`op.get_lt_str('%X')`。项目名大小写可能不同，不用大小写敏感断言唯一验证来源；加载返回值、路径和源数据都应核对。
- 沙箱会话可能启动不同用户环境，卡在 User Files Folder，或 shell 初始化失败。确有此证据时可通过正常权限机制在用户上下文运行同一命令。拒绝后报告阻碍，不能绕过；不擅自改注册表或杀用户进程。
- COM 返回 True 只代表命令分发成功。内置脚本写独立状态文件，检查 traceback、输出存在和数值验证，才能报告成功。

## 通用执行器

```powershell
python "<skill>/scripts/run_origin.py" --project "E:/sample.OPJ" --script "<skill>/scripts/inspect_project.py" --work "<workspace>/work/inspect1" -- "<workspace>/work/inventory.json"
```

`run_origin.py` 每次启动独立实例，保持窗口可见，不自动退出 Origin、不覆盖输入项目。`--work` 只存临时 wrapper/status 文件，不能用技能安装目录。每次使用不同 work 子目录。检查工作脚本自己的结果文件；包装器捕获并回传 Python 异常。工作脚本尽量在所有数据验证后创建最终结果和保存。

检查后制作处理脚本，再用同一输入项目执行；先前检查实例可留给用户，不关闭未知用户窗口。需要避免重复实例时，可自己保持一个外部 COM 引用，先 inspect，再处理；不要在 Origin 内置 Python 中无限轮询导致界面阻塞。

`originpro` 不在外部环境安装也能使用；脚本在 Origin 内运行。保留项目内部 Python 与外部 Python 的职责。优先使用 COM/原生 API；确需 GUI 操作才读取并使用可用的 computer-use 技能。

## 官方参考（仅在新增/不确定 API 时核对）

- https://docs.originlab.com/originpro/namespaceoriginpro_1_1project.html
- https://docs.originlab.com/originpro/classoriginpro_1_1worksheet_1_1WSheet.html
- https://docs.originlab.com/x-function/ref/smooth/
- https://docs.originlab.com/python/examples/graphing/
- https://docs.originlab.com/originpro/classoriginpro_1_1graph_1_1GPage.html
