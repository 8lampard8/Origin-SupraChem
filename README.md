# Origin-SupraChem

Fluorescence spectroscopy workflows for supramolecular chemistry and molecular sensing, delivered as the `origin-fluorescence` Codex skill.

面向超分子化学、分子识别与荧光传感研究的 Origin 光谱分析技能，支持从原始数据归档到可编辑科研图表的处理流程。适用对象包括氨基酸、其他有机分子、金属离子、阴离子及其他待测物；分析方案由实际实验设计与数据类型确定。

## 分析功能

- **光谱数据归档与实验分组**：依据样品标识、待测物种类和实验条件汇总，保留来源映射及原始元数据。
- **荧光滴定分析**：整理光谱随待测物当量、浓度或加入体积的变化，构建光谱序列与特征响应曲线；明确滴定变量及其单位。
- **发射光谱预处理**：调用 Origin 原生 Savitzky–Golay 算法；既有流程采用 25 点窗口、二阶多项式、无边界填充，参数可按实验需求调整。
- **光谱特征提取**：在指定波长区间提取局部峰及其峰位，支持平台峰与缺失峰报告；420 nm 仅作为参数示例。
- **响应离散性与重复性统计**：计算组间峰值的样本方差、总体方差及标准差；重复性评价要求相同实验条件下的重复测量。
- **待测物响应与对照比较**：按实验设计比较空白传感体系、不同待测物及相关对照；对手性体系可进一步比较 L/D、R/S 等对映体响应。
- **科研图表输出**：规范坐标、单位、物种命名及离子电荷上标，交付可编辑 Origin 项目和图像。

本项目提供技能指令与可复用辅助脚本。具体任务先核实样品语义、实验变量和单位，再选择适用的处理流程。结合常数、结合计量比、检出限或选择性结论需要相应实验设计、模型与验证，不能由常规平滑或对比图自动推定。

## 环境

- 实际 OPJ/OPJU 操作：Windows、合法安装并可用的 Origin/OriginPro，内置 `originpro`。
- 外部 Python 3.10+ 和 `pywin32`（`python -m pip install pywin32`）。
- 离线算法测试只需要 Python 标准库，不需要 Origin、SciPy 或实验数据。

测试过 OriginPro 2024b 的原生平滑流程；其他版本需实际验证。本项目不附带 Origin 软件、许可、实验数据或第三方代码。

## 安装为技能

将本仓库克隆或复制到个人技能目录下的 `origin-fluorescence` 文件夹，使 `SKILL.md` 位于该文件夹根目录。已有版本时先备份并对比本地修改。

```shell
git clone https://github.com/8lampard8/Origin-SupraChem.git ~/.codex/skills/origin-fluorescence
```

默认目录为 `~/.codex/skills/origin-fluorescence`；若配置了 `CODEX_HOME`，使用其 `skills` 子目录。

调用示例：

> 使用 $origin-fluorescence 对这个 OPJ 进行荧光滴定分析：按待测物当量汇总光谱，进行 25 点 SG 平滑，并在指定波段提取特征峰，绘制滴定响应曲线。

> 使用 $origin-fluorescence 按待测物种类汇总光谱，绘制传感体系空白及加入各待测物后的响应对比图；若为对映体识别实验，再按实际构型标签分组比较。

## 脚本

先读 `SKILL.md` 和 `references/origin-runtime.md`。

```powershell
python scripts/run_origin.py --project "C:/data/example.opju" --script scripts/inspect_project.py --work "work/inspect" -- "C:/work/inventory.json"
```

传入内置脚本的相对参数相对于 Origin 的工作目录，不保证是外部 shell 目录；实际使用时请提供绝对输出路径。不要运行来源不明的脚本。

每次执行器会启动新的可见实例，不覆盖原始项目。它不是批量绘图命令；具体模式见 `references/workflows.md`。`scripts/spectra.py` 可由任务脚本导入。

## 无实验数据的示例与测试

```shell
python examples/synthetic_peaks.py
python -m unittest discover -s tests -v
```

示例只使用代码生成的合成数据。自动测试验证寻峰边界、平台峰、方差分母及二阶 SG 内部一致性；不声称 CI 验证了专有软件的端点或图形界面。实际作图仍需 Origin 实测与导出图像检查。

## 持续维护

后续绘图中的可复用改进经验证后加入技能，见 `references/maintenance.md` 和 `CONTRIBUTING.md`。不发布实验文件、原始光谱、真实样品名称、个人绝对路径或凭据。公开更新前检查整个提交。

## License

MIT，见 `LICENSE`。与 OriginLab 无隶属关系。
