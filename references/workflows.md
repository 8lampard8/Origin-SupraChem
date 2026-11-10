# 模式配方

## 按当量分组

先把来源读成 `{book, sheet, original_label, series, equivalent, x, raw_y}`；分类后按数值当量排序，保留重复样品身份。等当量复测不擅自平均。

```python
book = op.new_book('w', lname='Grouped fluorescence')
book.name = 'GroupedXYZ'  # 若已存在，记录实际分配的名称，不假定此名称成功
sheet = book[0]
sheet.name = 'Spectra'
sheet.cols = 3 * len(records)
for j, r in enumerate(records):
    c = j * 3
    sheet.from_list(c, r['x'], lname='波长', units='nm', axis='X')
    sheet.from_list(c+1, [r['equivalent']]*len(r['x']), lname='当量', units='eq', axis='Y')
    sheet.from_list(c+2, r['raw_y'], lname='荧光强度', units='CPS', axis='Z')
sheet.cols_axis('xyz', 0, sheet.cols-1, True)
```

将各组原始值备份在内存或工作区，再调用 `spectra.smooth_column(sheet,c,c+2)`。算法只使用各组自己的 X 和强度，不把不同当量拼接后一起平滑。完成后设回列 L/U/C 和轴指定，因为算法可能修改标签。

## 峰值和方差

用 `spectra.highest_peak(x,y,threshold=420)`，返回 intensity/wavelength/row（行号为一基）或 None。它处理平台峰并要求峰两侧都有更低数据，选取最高峰。若用户明确要“区间最大值”则单独按该定义处理，不混称为局部峰。

新 Book 主表两列 X=当量，Y=峰值 CPS；来源详情放附表，含系列、原标签、峰位、源 Book/列/行。若是重复测量，用组号而非假造当量。

`spectra.variance_summary(values)` 对有限的组峰值返回 n、mean、sample_variance、population_variance、sample_sd。先报告缺失峰；不可悄悄删掉缺失后仍报告原始 n。

## 按氨基酸分类并绘图

明确当前主体全称及金属配比。核对每种氨基酸的 L/D 两种来源；缺失或多个复测先保留并告知，不用其他曲线填充。

建议一个 Book 包含：
- Raw：波长及所有原始光谱；波长完全一致才能共用 X，否则用各自 XY 列。
- Smoothed：对应平滑值，全部谱（包括主体）使用相同参数。
- 每类氨基酸表：X 波长，三条 Y：主体、主体+L、主体+D。
- 辅助扫描原始表：如 Data_S1/CPS 与 Data_R1/MicroAmps，明确未作一维平滑。

不需要把所有源项目内容删除；汇总只新建一个 Book 即可。不要照搬历史项目的谱数、286/311 行、14/15 类、Book 名称或 smz 缩写。

```python
g = op.new_graph(template='line', lname=class_title)
gl = g[0]
for c, color in zip([1, 2, 3], ['#30343B', '#D55E00', '#0072B2']):
    plot = gl.add_plot(sheet, coly=c, colx=0, type='line')
    plot.color = color
    plot.set_float('line.width', 2)
gl.rescale()
gl.axis('x').title = 'Wavelength (nm)'
gl.axis('y').title = 'Fluorescence intensity (CPS)'
legend = gl.label('Legend')
# 变量 labels 保存主体、主体+L、主体+D 的实际名称
legend.text = '\n'.join('\\l('+str(i)+') '+s.replace('Zn²⁺', r'Zn\+(2+)') for i,s in enumerate(labels,1))
legend.set_int('fsize', 13)
legend.set_int('showframe', 0)
g.set_int('aa', 1)
assert g.save_fig(str(png_path), width=2000)
```

依据实际曲线调整图例位置与坐标范围，不能默认 y 下限=0 截掉负信号。图间坐标是否统一取决于比较目的；默认不改变真实强度。使用 PIL 做全部图的检查拼图并逐张检查；若名称很长缩小字体或移图例，不缩写用户要求的主体全称。保存 OPJU 后将 PNG 打包 ZIP。

## 最小验收

- 先验证原始值、单位、有限点、递增波长及预期曲线数。
- 原生 SG 无填充边界只用 Origin 计算；`verify_sg_interior` 独立检验内部点，端点不能拿 SciPy 默认插值结果强行对齐。
- 全部原始源表、X 和当量列未变化；平滑列有正确行数及来源标签。
- 寻峰逐项回查源行并核对阈值；方差分别除以 n−1 和 n。
- `op.save()` 返回成功，目标文件非空，图像能解码且视觉检查通过。
