# Origin-SupraChem

Origin fluorescence workflows for supramolecular chemistry, packaged as the `origin-fluorescence` Codex skill. 用于 Origin 荧光光谱的分类汇总、平滑、提峰、统计和可编辑绘图。

## 功能

- 按样品、氨基酸 L/D 或当量分类；每个当量一组 XYZ。
- Origin 原生 Savitzky–Golay：默认 25 点、二阶、无边界填充。
- 波长严格大于阈值（默认 420 nm）的最高局部峰，支持平台峰和缺失峰报告。
- 组间峰值的样本方差、总体方差及标准差。
- 主体/L/D 三曲线，Zn²⁺ 上标，原始数据保留和图像核验。

这是技能与可复用辅助脚本，不是自动适配任何标签的全自动程序。Codex 会先检查来源、样品语义和单位，再按请求编写本次任务脚本。

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

> 使用 $origin-fluorescence 处理这个 OPJ：每个当量一组 XYZ，25 点平滑，提取 420 nm 后的最高局部峰。

> 使用 $origin-fluorescence 按氨基酸汇总，并绘制主体、主体+L、主体+D 三条曲线，金属离子的电荷使用上标。

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
