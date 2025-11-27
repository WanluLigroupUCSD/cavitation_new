#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import os  

def minimum_image_convention(v, box):
    return v - box * np.rint(v / box)

def read_xyz_frames(filename):
    try:
        with open(filename, 'r') as f:
            while True:
                num_atoms_line = next(f)
                num_atoms = int(num_atoms_line.strip())
                comment = next(f)
                atom_lines = [next(f) for _ in range(num_atoms)]
                if len(atom_lines) < num_atoms:
                    break
                yield (comment, atom_lines)
    except (StopIteration, ValueError):
        return
    except FileNotFoundError:
        print(f"错误: 输入文件 '{filename}' 未找到！")
        return

def calculate_cavity_probability_final(input_xyz, data_output_file,
                                       start_frame, box_dimensions, probe_radius,
                                       xy_grid_spacing, z_grid_spacing,
                                       z_scan_start, z_scan_end,
                                       oxygen_start_index=1, oxygen_end_index=None,
                                       reference_element='MO'):
    """
    在指定的绝对Z坐标范围内计算空腔概率，但以相对坐标输出结果。
    
    参数:
        oxygen_start_index: 要考虑的氧原子在所有原子中的起始位置编号 (从1开始，包含)
        oxygen_end_index: 要考虑的氧原子在所有原子中的结束位置编号 (从1开始，包含)，None表示到最后
        reference_element: 用作参考平面的元素名称 (例如 'MO', 'AU', 'PT' 等)
    """
    print(f"开始计算: 探测半径 R = {probe_radius} Å")
    print(f"将从第 {start_frame} 帧开始统计。")
    print(f"绝对Z轴扫描范围: 从 {z_scan_start} Å 到 {z_scan_end} Å")
    print(f"参考平面元素: {reference_element}")
    print(f"只考虑原子位置范围: 从第 {oxygen_start_index} 个原子到第 {oxygen_end_index if oxygen_end_index else '最后一个原子'}")

    box = np.array(box_dimensions)
    probe_radius_sq = probe_radius**2

    num_bins = int(np.ceil((z_scan_end - z_scan_start) / z_grid_spacing))
    total_probes_hist = np.zeros(num_bins, dtype=np.int64)
    empty_probes_hist = np.zeros(num_bins, dtype=np.int64)

    z_grid_absolute = np.arange(z_scan_start, z_scan_end, z_grid_spacing)
    x_grid = np.arange(0, box[0], xy_grid_spacing)
    y_grid = np.arange(0, box[1], xy_grid_spacing)
    
    frame_count = 0
    processed_frame_count = 0
    z_ref_list = [] 

    for comment, atom_lines in read_xyz_frames(input_xyz):
        frame_count += 1
        if frame_count < start_frame:
            continue

        processed_frame_count += 1
        if processed_frame_count % 100 == 0 and processed_frame_count > 0:
            print(f"  R={probe_radius}Å: 已处理 {processed_frame_count} 帧...")

        o_coords = []
        ref_coords = []  
        atom_index = 0  # 所有原子的全局计数器（从1开始）
        for line in atom_lines:
            parts = line.split()
            symbol = parts[0].upper()
            atom_index += 1  # 每读取一个原子，索引+1
            
            if symbol == 'O':
                # 检查该氧原子是否在指定的原子位置范围内
                if atom_index >= oxygen_start_index and (oxygen_end_index is None or atom_index <= oxygen_end_index):
                    o_coords.append([float(p) for p in parts[1:4]])
            elif symbol == reference_element.upper():
                ref_coords.append([float(p) for p in parts[1:4]])
        
        o_coords_np = np.array(o_coords)
        if not ref_coords: continue
        
        current_z_ref = np.mean([coords[2] for coords in ref_coords])
        z_ref_list.append(current_z_ref)
        
        for i_z, gz in enumerate(z_grid_absolute):
            for gx in x_grid:
                for gy in y_grid:
                    total_probes_hist[i_z] += 1
                    grid_point = np.array([gx, gy, gz])

                    diffs = minimum_image_convention(o_coords_np - grid_point, box)
                    dists_sq = np.sum(diffs**2, axis=1)

                    if np.all(dists_sq > probe_radius_sq):
                        empty_probes_hist[i_z] += 1
    
    print(f"  R={probe_radius}Å: 分析完成！共处理 {processed_frame_count} 帧。")

    avg_z_ref = np.mean(z_ref_list)
    
    total_probes_safe = np.where(total_probes_hist == 0, 1, total_probes_hist)
    probability = empty_probes_hist / total_probes_safe
    
    z_axis_absolute = z_grid_absolute + z_grid_spacing / 2.0
    z_axis_relative = z_axis_absolute - avg_z_ref

    results = np.vstack([z_axis_relative, probability, empty_probes_hist, total_probes_hist]).T
    np.savetxt(data_output_file, results,
               header="z_relative(A)  P(0)  empty_counts  total_counts",
               fmt="%.6f")
    print(f"  R={probe_radius}Å: 数据已保存到: {data_output_file}")
    
    return np.sum(empty_probes_hist), np.sum(total_probes_hist)


if __name__ == '__main__':
    input_file = 'output_shifted_traj_ordered.xyz'
    start_frame = 2000
    box_dimensions = [16.4721,12.6818,35.3541] 
    xy_grid_spacing = 1
    z_grid_spacing = 0.1
    z_scan_start = 0.0
    z_scan_end = 20
    
    oxygen_start_index = 1      
    oxygen_end_index = None     
    reference_element = 'MO'    
    

    KB = 1.380649e-23
    NA = 6.02214076e23
    TEMP_K = 298.15
    KT_KJ_MOL = (KB * TEMP_K * NA) / 1000.0


    probe_radii_to_test_A = [1.5, 1.75, 2.0, 2.25, 2.5] 
    
    summary_data = []


    for radius in probe_radii_to_test_A:
        print(f"\n=======================================================")
        print(f"开始处理新的半径: R = {radius} Å")

        dir_name = f"R={radius}"
        os.makedirs(dir_name, exist_ok=True) 

        data_file_path = os.path.join(dir_name, 'cavity_probability.dat')

        global_empty, global_total = calculate_cavity_probability_final(
            input_file, data_file_path,
            start_frame, box_dimensions,
            radius, xy_grid_spacing, 
            z_grid_spacing, z_scan_start, z_scan_end,
            oxygen_start_index, oxygen_end_index,
            reference_element
        )
        
        if global_total > 0:
            p0_global = global_empty / global_total
        else:
            p0_global = 0.0
            
        if p0_global > 0:
            delta_g = -KT_KJ_MOL * np.log(p0_global)
        else:
            delta_g = np.inf 
            
        summary_data.append({
            'Radius(Å)': radius,
            'P0': p0_global,
            'FreeEnergy(kJ/mol)': delta_g
        })
                                           
    print(f"\n=======================================================")
    print("所有半径均已处理完毕！")
    
    summary_df = pd.DataFrame(summary_data)
    summary_output_file = 'cavitation_energy_summary.csv'
    summary_df.to_csv(summary_output_file, index=False)
    print(f"汇总数据已保存到: {summary_output_file}")
    print(summary_df)
