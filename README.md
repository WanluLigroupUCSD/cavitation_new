# cavitation_new
a python program to calculate cavitation energy

# 空腔概率与空化自由能计算脚本

## 功能概述

`cavity_Probability_multy_radius.py` 是一个用于计算水溶液体系中空腔形成概率和空化自由能的Python脚本。该脚本可以：

- 在指定的空间区域内计算不同半径探测球的空腔概率
- 支持多个探测半径的批量计算
- 计算空化自由能（创建空腔所需的能量代价）
- 生成空腔概率随Z轴位置的分布数据
- 灵活选择要分析的氧原子范围和参考平面元素

## 依赖库

```bash
pip install numpy pandas
```

所需Python库：
- `numpy` - 数值计算
- `pandas` - 数据处理和CSV输出

## 输入文件要求

**输入文件格式**: XYZ轨迹文件

```
<原子数>
<注释行>
O  x1  y1  z1
O  x2  y2  z2
MO x3  y3  z3
...
```

- 每帧包含原子数、注释和原子坐标
- 支持的原子类型：氧原子(O)和参考平面元素(如MO, AU, PT等)

## 参数配置

打开脚本文件，在 `if __name__ == '__main__':` 部分修改以下参数：

### 1. 基本参数

```python
# 输入文件
input_file = 'output_shifted_traj_ordered.xyz'  # XYZ轨迹文件名

# 模拟参数
start_frame = 2000                              # 从第几帧开始统计
box_dimensions = [16.4721, 12.6818, 35.3541]    # 模拟盒子尺寸 [x, y, z] (Å)

# 格点设置
xy_grid_spacing = 1      # XY平面格点间距 (Å)
z_grid_spacing = 0.1     # Z轴格点间距 (Å)

# Z轴扫描范围（绝对坐标）
z_scan_start = 0.0       # Z轴扫描起始位置 (Å)
z_scan_end = 20          # Z轴扫描结束位置 (Å)
```

### 2. 氧原子选择范围

```python
# 指定要考虑的氧原子在所有原子中的位置范围（从1开始编号）
oxygen_start_index = 1      # 起始原子位置编号（包含）
oxygen_end_index = None     # 结束原子位置编号（包含），None表示到最后一个原子
```

**重要说明**：
- 这些参数指定的是**氧原子在XYZ文件中所有原子的位置范围**，而不是只数氧原子
- 脚本会检查该范围内的原子，只保留其中为氧原子的部分

**使用场景**：

假设你的XYZ文件结构如下：
```
原子1-100:   水分子的O原子
原子101-200: 其他分子的O原子
原子201-250: MO原子（参考平面）
```

- **分析所有氧原子**：
  ```python
  oxygen_start_index = 1
  oxygen_end_index = None  # 或者 200
  ```

- **只分析水分子的氧原子**：
  ```python
  oxygen_start_index = 1
  oxygen_end_index = 100
  ```

- **只分析其他分子的氧原子**：
  ```python
  oxygen_start_index = 101
  oxygen_end_index = 200
  ```

**注意**：如果指定范围内没有氧原子（例如把范围设在MO原子区域），脚本不会报错，但会认为整个区域都是空腔（P0=1.0）

### 3. 参考平面元素

```python
# 指定用作参考平面的元素
reference_element = 'MO'    # 参考平面元素名称（如 'MO', 'AU', 'PT' 等）
```

**说明**：脚本会计算参考平面元素在每帧中的平均Z坐标，作为相对坐标系的原点。

### 4. 探测半径设置

```python
# 设置要测试的一系列探测半径 (单位: Å)
probe_radii_to_test_A = [1.5, 1.75, 2.0, 2.25, 2.5]
```

**说明**：脚本会对列表中的每个半径分别进行计算。

### 5. 物理常数

```python
# 温度设置
TEMP_K = 298.15    # 温度 (K)
```

其他常数（通常不需修改）：
- `KB` - 玻尔兹曼常数
- `NA` - 阿伏伽德罗常数
- `KT_KJ_MOL` - kT 值（单位：kJ/mol）

## 运行脚本

```bash
python cavity_Probability_multy_radius.py
```

## 输出文件

### 1. 各半径的详细数据

每个探测半径会创建一个独立文件夹，包含详细的空腔概率分布：

```
R=1.5/
  └── cavity_probability.dat
R=1.75/
  └── cavity_probability.dat
R=2.0/
  └── cavity_probability.dat
...
```

**文件格式** (`cavity_probability.dat`)：
```
# z_relative(A)  P(0)  empty_counts  total_counts
-10.234500  0.856234  8562  10000
-10.134500  0.862145  8621  10000
...
```

列说明：
- `z_relative(A)` - 相对于参考平面的Z坐标 (Å)
- `P(0)` - 该位置的空腔概率
- `empty_counts` - 该位置的空腔计数
- `total_counts` - 该位置的总探测次数

### 2. 汇总数据

**文件名**: `cavitation_energy_summary.csv`

包含所有半径的全局统计数据：

| Radius(Å) | P0 | FreeEnergy(kJ/mol) |
|-----------|----|--------------------|
| 1.5 | 0.125 | 5.12 |
| 1.75 | 0.089 | 6.05 |
| 2.0 | 0.045 | 7.58 |
| ... | ... | ... |

列说明：
- `Radius(Å)` - 探测半径
- `P0` - 全局空腔概率
- `FreeEnergy(kJ/mol)` - 空化自由能

## 物理意义

### 空腔概率 P0
在模拟过程中，一个半径为 R 的球形区域不被氧原子占据的概率。

- **P0 → 1**: 该区域容易形成空腔，水分子密度低
- **P0 → 0**: 该区域难以形成空腔，水分子密度高

### 空化自由能 ΔG

$$\Delta G_{cav} = -k_B T \ln P_0$$

表示在溶液中创建一个半径为 R 的空腔所需的自由能变化（能量代价）。

- **ΔG 大**: 形成空腔困难，需要大量能量排开水分子
- **ΔG 小**: 形成空腔容易，该区域本来就相对空旷

## 使用示例

### 示例1：分析水分子在金(AU)表面的分布

```python
# 基本参数
input_file = 'gold_surface_water.xyz'
box_dimensions = [20.0, 20.0, 40.0]
start_frame = 1000

# 只考虑文件中前200个原子位置上的氧原子（假设1-200位置是水分子）
oxygen_start_index = 1
oxygen_end_index = 200

# 使用金原子作为参考平面
reference_element = 'AU'

# 测试多个半径
probe_radii_to_test_A = [1.0, 1.5, 2.0, 2.5, 3.0]
```

### 示例2：分析纳米孔内的水分子

```python
# 基本参数
input_file = 'nanopore_water.xyz'
box_dimensions = [15.0, 15.0, 50.0]

# 只分析文件中第100-500个原子位置上的氧原子（孔道内部的水分子）
oxygen_start_index = 100
oxygen_end_index = 500

# 使用碳纳米管的碳原子作为参考
reference_element = 'C'
```

## 注意事项

1. **内存使用**: 大型轨迹文件可能消耗大量内存，建议适当增大 `start_frame` 跳过前期平衡阶段
2. **格点间距**: `xy_grid_spacing` 和 `z_grid_spacing` 越小，计算越精确但速度越慢
3. **周期性边界**: 代码使用最小镜像约定处理周期性边界条件
4. **参考元素**: 确保 `reference_element` 在轨迹文件中存在，否则会跳过该帧

## 输出进度

运行时会显示进度信息：

```
=======================================================
开始处理新的半径: R = 1.5 Å
开始计算: 探测半径 R = 1.5 Å
将从第 2000 帧开始统计。
绝对Z轴扫描范围: 从 0.0 Å 到 20 Å
参考平面元素: MO
只考虑原子位置范围: 从第 1 个原子到第 最后一个原子
  R=1.5Å: 已处理 100 帧...
  R=1.5Å: 已处理 200 帧...
  ...
  R=1.5Å: 分析完成！共处理 5000 帧。
  R=1.5Å: 数据已保存到: R=1.5/cavity_probability.dat
=======================================================
```

## 数据可视化建议

使用以下Python代码绘制结果：

```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取汇总数据
df = pd.read_csv('cavitation_energy_summary.csv')

# 绘制自由能随半径的变化
plt.figure(figsize=(8, 6))
plt.plot(df['Radius(Å)'], df['FreeEnergy(kJ/mol)'], 'o-')
plt.xlabel('Probe Radius (Å)')
plt.ylabel('Cavitation Free Energy (kJ/mol)')
plt.title('Cavitation Free Energy vs Probe Radius')
plt.grid(True)
plt.savefig('cavitation_energy.png', dpi=300)
plt.show()

# 读取某个半径的详细分布
data = pd.read_csv('R=2.0/cavity_probability.dat', delim_whitespace=True, comment='#')
plt.figure(figsize=(8, 6))
plt.plot(data['z_relative(A)'], data['P(0)'])
plt.xlabel('Z position relative to surface (Å)')
plt.ylabel('Cavity Probability P(0)')
plt.title('Cavity Probability Profile (R=2.0Å)')
plt.grid(True)
plt.savefig('cavity_profile_R2.0.png', dpi=300)
plt.show()
```

## 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|----------|---------|
| 脚本运行很慢 | 格点间距太小或轨迹太长 | 增大格点间距或增加 start_frame |
| 输出 P0=0.0 | 探测半径太大或氧原子太密集 | 减小探测半径或检查氧原子选择范围 |
| 没有生成文件 | 参考元素不存在 | 检查 reference_element 是否正确 |
| 内存不足 | 轨迹文件太大 | 分批处理或增加 start_frame |

## 作者与版权

本脚本用于计算化学和分子模拟领域的空腔分析。

## 更新日志

- **v1.0**: 初始版本，支持基本空腔概率计算
- **v2.0**: 添加氧原子范围选择和参考平面元素自定义功能
- **v2.1**: 氧原子选择改为基于所有原子中的绝对位置，而非相对氧原子编号
