import os
import sys
import open3d as o3d
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, Menu
import math
from blank_module import calculate_grid_median_with_kdtree, las2Array, read_las_file, pickfile, key_callback_1, get_optimal_gridsize
import multiprocessing 
import time
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image, ImageTk,ImageSequence
import threading
import queue
import subprocess


def create_gui():
    root = tk.Tk()
    root.title("SeaDan")
    root.geometry("1000x650")

    header_frame = tk.Frame(root, bg="#ffffff", height=50)
    header_frame.pack(fill="x")
    
    content_frame = tk.Frame(root, bg="#F5F5F5")
    content_frame.pack(fill="both", expand=True)

    menubar = Menu(root)
    root.config(menu=menubar)
    # menubar.add_command(label="File")

    tool_menus = Menu(menubar, tearoff=0)
    about_menus = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Tools", menu=tool_menus)
    menubar.add_cascade(label="About", menu=about_menus)
    
    try:
        image = Image.open('./image/tse.png')
    except:
        try:
            image = Image.open('./blankspace/image/tse.png')
        except:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            print(script_dir)
            image = Image.open(script_dir.rstrip("SeaDan-Flow")+"image\\tse.png")
    image = image.resize((80, 40))  # ปรับขนาดรูปภาพ
    photo = ImageTk.PhotoImage(image)
    
    image_label = tk.Label(header_frame, image=photo) #bg='#ADE1FB'
    image_label.image = photo  # เก็บอ้างอิงรูปภาพเพื่อไม่ให้ถูกลบ
    image_label.pack(side="right", padx=20, pady=20)
    
    header_label = tk.Label(header_frame, text="SeaDan", font=("Helvetica", 20, 'bold'),bg='#FFF9F0',fg="#0F2573") 
    header_label.pack(side="left", padx=20, pady=20)
    
    pcd1 = None
    pcd2 = None
    matrix2 = np.eye(4)
    step_value = tk.DoubleVar(value=0.05)
    grid_value = tk.DoubleVar(value=1)
    last_loaded_file1 = None  
    last_loaded_file2 = None

    def change_calculate_btn_state():
        if pcd1 is not None:
            start_vis_source.state(['!disabled'])
        
        if pcd2 is not None:
            start_vis_target.state(['!disabled'])
            
        if pcd1 is not None and pcd2 is not None:
            start_calculate_btn.state(['!disabled'])
            start_viewer_btn.state(['!disabled'])
            tool_menus.entryconfig("Optimal Grid Size", state="normal")
    
    def load_file1():
        nonlocal pcd1,last_loaded_file1
        file_path = pickfile("source")
        if file_path:
            if file_path == last_loaded_file1:  
                messagebox.showinfo("Info", "File 1 is already loaded.")
                return
            try:
                las_data, pcd = read_las_file(file_path)
                points, colors = las2Array(las_data)
                pcd.points = o3d.utility.Vector3dVector(points)
                pcd.colors = o3d.utility.Vector3dVector(colors)
                pcd1 = pcd
                last_loaded_file1 = file_path  
                file_name1.config(text=f"✅ {file_path.split('/')[-1]}")


                point_count_label1 = tk.Label(file1_frame, text="Points",bg="#f5f5f5")
                point_count_label1.grid(row=1, column=0, pady=1, padx=5, sticky='w')
                point_count_value1 = tk.Label(file1_frame, text=f"{len(pcd1.points):,.0f}", bg='#f5f5f5')
                point_count_value1.grid(row=1, column=1, pady=1, padx=5, sticky='w')

                pcd1_size_label = tk.Label(file1_frame, text="Data size", bg='#f5f5f5')
                pcd1_size_label.grid(row=2,column=0, padx=5, pady=1, sticky='w')
                pcd1_size = tk.Label(file1_frame, text=f"{(points.nbytes+colors.nbytes+sys.getsizeof(pcd))/(1024 * 1024):,.4f} MB", bg='#f5f5f5') # points + pcd.colors + object overhead
                pcd1_size.grid(row=2, column=1, padx=5, pady=1, sticky='w')

                progress_bar.grid_forget()
                change_calculate_btn_state()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                progress_bar.grid_forget()

    def load_file2():
        nonlocal pcd2,last_loaded_file2
        file_path = pickfile("target")
        if file_path:
            if file_path == last_loaded_file2:  
                messagebox.showinfo("Info", "File 2 is already loaded.")
                return

            try:

                las_data, pcd = read_las_file(file_path)
                points, colors = las2Array(las_data)
                pcd.points = o3d.utility.Vector3dVector(points)
                pcd.colors = o3d.utility.Vector3dVector(colors)
                pcd2 = pcd
                last_loaded_file2 = file_path  
                file_name2.config(text=f"✅ {file_path.split('/')[-1]}")  

                point_count_label2 = tk.Label(file2_frame, text="Points",bg="#f5f5f5")
                point_count_label2.grid(row=1, column=0, pady=1, padx=5, sticky='w')
                point_count_value2 = tk.Label(file2_frame, text=f"{len(pcd2.points):,.0f}", bg='#f5f5f5')
                point_count_value2.grid(row=1, column=1, pady=1, padx=5, sticky='w')

                pcd2_size_label = tk.Label(file2_frame, text="Data size", bg='#f5f5f5')
                pcd2_size_label.grid(row=2,column=0, padx=5, pady=1, sticky='w')
                pcd2_size = tk.Label(file2_frame, text=f"{(points.nbytes+colors.nbytes+sys.getsizeof(pcd))/(1024 * 1024):,.4f} MB", bg='#f5f5f5')
                pcd2_size.grid(row=2, column=1, padx=5, pady=1, sticky='w')

                progress_bar.grid_forget()
                change_calculate_btn_state()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                progress_bar.grid_forget()
    
    def open_optimal_grid_size_window():
        nonlocal pcd1, pcd2, grid_value
        window = tk.Toplevel()
        window.title("Optimal Grid Size")
        window.geometry("300x150")
        opt_grid_label = tk.Label(window, text="Optimal Grid Size: ", font=("Arial", 10), bg="#F5F5F5")
        opt_grid_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')
        optimal_grid_size_text = tk.Text(window, wrap='word', font=("Arial", 10), width=15, height=1)
        optimal_grid_size_text.grid(row=0, column=1, padx=10, pady=10, sticky='we')

        optimal_grid_size_text.insert(tk.END, "Optimal Grid Size")
        optimal_grid_size_text.config(state=tk.DISABLED)

        cal_optimal_grid_size_btn = ttk.Button(window, text="get optimal grid size", command=lambda: on_grid_size_click(pcd1, pcd2))
        cal_optimal_grid_size_btn.grid(row=1, column=1, padx=10, pady=10, sticky='w')


        def on_grid_size_click(pcd1, pcd2):
            grid_size = get_optimal_gridsize(pcd1, pcd2)
            optimal_grid_size_text.config(state=tk.NORMAL)
            optimal_grid_size_text.delete(1.0, tk.END)
            optimal_grid_size_text.insert(tk.END, grid_size)
            optimal_grid_size_text.config(state=tk.DISABLED)
            apply_grid_size_btn = ttk.Button(window, text="Apply", command=lambda: grid_value.set(grid_size))
            apply_grid_size_btn.grid(row=2, column=1, padx=10, pady=10, sticky='w')

    tool_menus.add_command(label="Optimal Grid Size", command=open_optimal_grid_size_window, state='disabled'   )
    tool_menus.add_command(label="Merge & Cut", command=run_merge_cut_script)

    files_frame = tk.Frame(content_frame, bg="#F5F5F5")
    files_frame.grid(row=0, column=0, padx=10, pady=10)

    file1_frame = tk.LabelFrame(files_frame, text="Time Series1 / Before", bg="#F5F5F5")
    file1_frame.grid(row=0, sticky='we')
    file2_frame = tk.LabelFrame(files_frame, text="Time Series2 / After", bg="#F5F5F5")
    file2_frame.grid(row=1, sticky="we")


    file1_label = tk.Label(file1_frame, text="File", bg="#F5F5F5")
    file1_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
    file2_label = tk.Label(file2_frame, text="File", bg="#F5F5F5")
    file2_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
    
    load_btn1 = ttk.Button(file1_frame, text="📄 Open File", command=load_file1, width=15) #Load Time Series 1
    load_btn1.grid(row=0, column=2 , pady=10, padx=10)

    load_btn2 = ttk.Button(file2_frame, text="📄 Open File", command=load_file2, width=15) #Load Time Series 2
    load_btn2.grid(row=0, column=2, pady=10, padx=10)

    calculator_frame = tk.LabelFrame(content_frame, text="Calculate Volume", bg="#F5F5F5")
    calculator_frame.grid(row=2, column=0, padx=10, pady=10, sticky="we")
    
    
    file_name1 = tk.Label(file1_frame, text="❌ No file loaded", fg="blue",bg="#f5f5f5")
    file_name1.grid(row=0, column=1, pady=5, padx=5, sticky='w')
    
    file_name2 = tk.Label(file2_frame, text="❌ No file loaded", fg="blue",bg="#f5f5f5")
    file_name2.grid(row=0, column=1, pady=5, padx=5, sticky='w')
    
    visualize_and_align_frame = tk.LabelFrame(content_frame, text="Visualization & Align", bg="#F5F5F5")
    visualize_and_align_frame.grid(row=1, column=0, padx=10, pady=10, sticky="we")

    step_label = tk.Label(visualize_and_align_frame, text="Step value :", font=("Helvetica", 14), bg="#f5f5f5", fg="#0F2573")
    step_label.grid(row=0,column=0, padx=5, pady=5)
    
    step_entry = tk.Entry(visualize_and_align_frame, textvariable=step_value)
    step_entry.grid(row=0,column=1, padx=5, pady=5)
    
    grid_size = tk.Label(calculator_frame, text="Grid size :", font=("Helvetica", 14), bg="#f5f5f5", fg="#0F2573")
    grid_size.grid(row=0,column=0, padx=5)
    
    grid_entry = tk.Entry(calculator_frame, textvariable=grid_value)
    grid_entry.grid(row=0,column=1, padx=5, sticky='we')

    progress_bar = ttk.Progressbar(calculator_frame, length=200, mode="determinate")
    progress_bar.grid(row=1, column=2, columnspan=2, padx=5, pady=5)
    progress_bar.grid_remove()  # ซ่อนไว้ก่อน

    start_vis_source = ttk.Button(file1_frame, text="Visualize Original", command=lambda: visualize_a_point_cloud(pcd1, "Time Series1"), state='disabled')
    start_vis_target = ttk.Button(file2_frame, text="Visualize Original", command=lambda: visualize_a_point_cloud(pcd2, "Time Series2"), state='disabled')
    start_vis_source.grid(row=0, column=3, pady=10, padx=5)
    start_vis_target.grid(row=0, column=3, pady=10, padx=5)

    start_viewer_btn = ttk.Button(visualize_and_align_frame, state='disabled', text="Visualize & Align", command=lambda: start_viewer(pcd1, pcd2, step_value.get()))
    start_viewer_btn.grid(row=1, column=1, pady=5, padx=5, sticky="we")

    progress_queue = queue.Queue()
    start_calculate_btn = ttk.Button(calculator_frame, text="🚀 Start Calculate", command=lambda:[
        stop_animation.clear(),
        threading.Thread(target=start_calculate, args=(pcd1, pcd2, progress_queue, grid_value.get())).start(),
        start_progress(stop_animation, progress_queue)
    ], state='disabled')
    start_calculate_btn.grid(row=1, column=1, pady=10, padx=5, sticky="we")

    man_btn = ttk.Button(visualize_and_align_frame, text="❔manual", command=show_man)
    man_btn.grid(row=2, column=1, pady=5, padx=5, sticky="we")

    matrix_btn = ttk.Button(visualize_and_align_frame, text="📋 Show Matrix", command=lambda: show_matrix(np))
    matrix_btn.grid(row=3, column=1, pady=5, padx=5, sticky="we")


    history_data = []  # ลิสต์สำหรับเก็บประวัติการคำนวณ

    def show_history():
        history_window = tk.Toplevel(root)  # สร้างหน้าต่างใหม่สำหรับประวัติ
        history_window.title("History of Calculations")
        history_window.geometry("600x400")
        
        history_text = tk.Text(history_window, height=100, width=100, wrap="word", font=("Arial", 12))
        history_text.pack(pady=10)

        history_text.insert(tk.END, "Calculation History:\n")
        if len(history_data) == 0:
            history_text.insert(tk.END, "No history data available.")  # ถ้าไม่มีข้อมูลให้แสดงข้อความนี้
        for entry in history_data:
            history_text.insert(tk.END, f"{entry}\n\n")
        history_text.config(state=tk.DISABLED)
    
    # def animate_gif(canvas, gif_sequence, gif_id, stop_flag):
    #     frame_index = 0

    #     def next_frame():
    #         nonlocal frame_index
    #         if stop_flag.is_set():  # ถ้าถูกตั้งค่าให้หยุด ออกจากแอนิเมชัน
    #             return
    #         frame_index = (frame_index + 1) % len(gif_sequence)
    #         canvas.itemconfig(gif_id, image=gif_sequence[frame_index])
    #         canvas.after(100, next_frame)

    #     next_frame()
        
    def start_calculate(src_pcd, target_pcd,progress_queue, grid_size=1.0):
        total_steps = 10
        current_step = 0
        src_points = np.asarray(src_pcd.points)
        tgt_points = np.asarray(target_pcd.points)
        
        def update_progress():
            nonlocal current_step
            current_step += 1
            percentage = int((current_step / total_steps) * 100)
            progress_queue.put(percentage)
            
        update_progress()

        src_x_min, src_x_max = min(src_points[:, 0]), max(src_points[:, 0])
        src_y_min, src_y_max = min(src_points[:, 1]), max(src_points[:, 1])
        tgt_x_min, tgt_x_max = min(tgt_points[:, 0]), max(tgt_points[:, 0])
        tgt_y_min, tgt_y_max = min(tgt_points[:, 1]), max(tgt_points[:, 1])
        
        update_progress()

        gbl_x_min, gbl_x_max = min(src_x_min, tgt_x_min), max(src_x_max, tgt_x_max)
        gbl_y_min, gbl_y_max = min(src_y_min, tgt_y_min), max(src_y_max, tgt_y_max)
        
        update_progress()

    # Calculate the total width and height in meters
        width_meters = gbl_x_max - gbl_x_min
        height_meters = gbl_y_max - gbl_y_min

        col_width = grid_size
        row_width = grid_size
        
        n_cols = math.ceil((gbl_x_max - gbl_x_min) / col_width)
        n_rows = math.ceil((gbl_y_max - gbl_y_min) / row_width)

        start_time = time.perf_counter()
        
        update_progress()

        src_args = (src_points, gbl_x_min, gbl_y_min, col_width, row_width, n_rows, n_cols)
        tgt_args = (tgt_points, gbl_x_min, gbl_y_min, col_width, row_width, n_rows, n_cols)
    
        src_z_min, src_z_max = np.min(src_points[:, 2]), np.max(src_points[:, 2])
        tgt_z_min, tgt_z_max = np.min(tgt_points[:, 2]), np.max(tgt_points[:, 2])

    # คำนวณ Global Altitude Range
        gbl_z_min = min(src_z_min, tgt_z_min)  # ความสูงต่ำสุด
        gbl_z_max = max(src_z_max, tgt_z_max)  # ความสูงสูงสุด
        
        update_progress()

        if n_cols * n_rows < 1:
        # Use multiprocessing to calculate median altitudes for both source and target
            with multiprocessing.Pool(processes=4) as pool:
                results = pool.starmap(calculate_grid_median_with_kdtree, [src_args, tgt_args])
                pool.close() 
                pool.join()
        # Unpack results
            src_avg_alt_mat, count_point_src = results[0]
            tgt_avg_alt_mat, count_point_tgt = results[1]
        else:
            src_avg_alt_mat, count_point_src = calculate_grid_median_with_kdtree(*src_args)
            tgt_avg_alt_mat, count_point_tgt = calculate_grid_median_with_kdtree(*tgt_args)

        print(count_point_src)
        print(count_point_tgt)
        
        update_progress()

    # Delta altitude matrix and volume change calculation
        delta_alt_mat = tgt_avg_alt_mat - src_avg_alt_mat
        cell_area = col_width * row_width
        
        update_progress()

        volume_change = delta_alt_mat * cell_area
        volume_change = np.nan_to_num(volume_change)
        total_volume_change = np.sum(volume_change)

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        
        update_progress()
            
        # Transformation Metrics (using ICP)
        reg_icp = o3d.pipelines.registration.registration_icp(
            # src_pcd, target_pcd, 0.005, np.eye(4),
            target_pcd, src_pcd, 0.005, np.eye(4),
            o3d.pipelines.registration.TransformationEstimationPointToPoint()
        )
        transformation_matrix = reg_icp.transformation
        
        update_progress()
        
        stop_animation.set()  
        
        sand_increase = np.sum(delta_alt_mat[delta_alt_mat > 0.1] * cell_area)
        sand_decrease = np.sum(delta_alt_mat[delta_alt_mat < -0.1] * cell_area)
        
        q = queue.Queue()
        
        q.put((src_avg_alt_mat, tgt_avg_alt_mat, delta_alt_mat, gbl_z_min, gbl_z_max, width_meters, height_meters, sand_increase, sand_decrease, count_point_src, count_point_tgt, total_volume_change, elapsed_time,transformation_matrix,step_value.get(),col_width, row_width))
        
        result_frame = tk.LabelFrame(content_frame, text="Result", bg="#f5f5f5")
        result_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky='wsne')
        result_frame_r0 = tk.Frame(result_frame, bg="#f5f5f5")
        result_frame_r0.grid(row=0, column=0, sticky='w')
        result_frame_r2 = tk.Frame(result_frame, bg="#f5f5f5")
        result_frame_r2.grid(row=2, column=0, sticky='w')

        def reset_gui():
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.config(state=tk.DISABLED)
        
            # load_btn1.config(fg="#0F2573", text="📂 Load Time Series1")
            # load_btn2.config(fg="#0F2573", text="📂 Load Time Series2")
        
            global src_file, tgt_file
            src_file = None
            tgt_file = None

        style = ttk.Style()
        style.configure("danger.TButton")
        style.map("danger.TButton",
                    foreground=[
                        ("!active", "#ef4444"),
                        ("active", "#ef4444")
                    ],
                )

        reset_btn = ttk.Button(
            result_frame_r2,
            text="Reset", 
            command=reset_gui,
            style="danger.TButton",
        )
        reset_btn.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        graph = ttk.Button(result_frame_r0, text="📊 Graph", command=lambda:plot_graph(src_avg_alt_mat, tgt_avg_alt_mat, delta_alt_mat, gbl_z_min, gbl_z_max, width_meters, height_meters, sand_increase, sand_decrease))
        graph.grid(row=0, column=0, padx=5, pady=5, sticky='w')
          
        view = ttk.Button(result_frame_r0, text="Volume Change", command=lambda: view_all(pcd1,pcd2))
        view.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ts1 = ttk.Button(file1_frame, text="Heat Map",command=lambda:visualize_a_point_cloud_color(pcd1, "Time Series1",apply_cmap=True)) #Time Series 1
        ts1.grid(row=0, column=4,padx=5)
        
        ts2 = ttk.Button(file2_frame, text="Heat Map",command=lambda:visualize_a_point_cloud_color(pcd2, "Time Series2",apply_cmap=True)) #Time Series 2
        ts2.grid(row=0, column=4,padx=5)
        
        def view_all(pcd1, pcd2, threshold_min=-0.1, threshold_max=0.1):
                try:
                    temp_file1 = "pcd1_volume.ply"
                    temp_file2 = "pcd2_volume.ply"

                    o3d.io.write_point_cloud(temp_file1, pcd1)
                    o3d.io.write_point_cloud(temp_file2, pcd2)

                    subprocess.Popen(["python", "visualize_volume.py", temp_file1, temp_file2, str(threshold_min), str(threshold_max)], start_new_session=True)
                except:
                    messagebox.showwarning("Error", "กรุณาเลือกไฟล์ LAS ก่อน")
        
                
        def visualize_a_point_cloud_color(pcd, title, apply_cmap=False):
            try:
                temp_file = f"{title}_color.ply"
                o3d.io.write_point_cloud(temp_file, pcd)

                subprocess.Popen(["python", "visualize_color.py", temp_file, title, str(apply_cmap)], start_new_session=True)
    
            except:
                messagebox.showwarning("Error", "กรุณาเลือกไฟล์ LAS ก่อน")
        
        def copy_to_clipboard():
            text = result_text.get("1.0", tk.END).strip()  # ดึงข้อความทั้งหมดจาก Text widget
            if text:
                root.clipboard_clear()  # ล้างข้อมูลเก่าบนคลิปบอร์ด
                root.clipboard_append(text)  # เพิ่มข้อความใหม่ในคลิปบอร์ด
                root.update()  # อัปเดต GUI
                messagebox.showinfo("Success", "Text copied to clipboard!")  # แสดงข้อความแจ้งเตือน
            else:
                messagebox.showwarning("Warning", "No text to copy!")
                graph = tk.Button(root, text="Graph", command=lambda:plot_graph(src_avg_alt_mat, tgt_avg_alt_mat, delta_alt_mat, gbl_z_min, gbl_z_max, width_meters, height_meters, sand_increase, sand_decrease), width=22, height=2)
                graph.grid(row=4, pady=10, padx=5,rowspan=2)
        
        calculation_result = (f"Transformation Metrics:\n\n{np.array2string(transformation_matrix, formatter={'float_kind': lambda x: f'{x:.2f}'})}\n\n"
                      f"Total Volume Change: {total_volume_change:.2f} m³\nElapsed Time: {elapsed_time:.2f} seconds\n"
                      f"Global Altitude Range: {gbl_z_min:.2f} to {gbl_z_max:.2f}\n"
                      f"-----------------------------------------------------------------------------------------------------------------------")

        history_data.append(calculation_result)
        print("History Entry Added:", calculation_result)  # ตรวจสอบข้อมูลที่เพิ่มเข้าไป

        result_text = tk.Text(result_frame, height=10, width=30, wrap="word", font=("Arial", 12))
        result_text.grid(row=1, column=0, padx=5, pady=5)

        result_text.config(state=tk.NORMAL)
        result_text.tag_configure("center", justify="center")
        # result_text.insert(tk.END, f"\n{np.array2string(transformation_matrix, formatter={'float_kind': lambda x: f'{x:.2f}'})}\n\n\n")
        result_text.insert(tk.END, calculation_result.rstrip('-').rstrip('\n'))
        result_text.config(state=tk.DISABLED)
        copy_label = ttk.Button(result_frame_r2, text="📋 Copy", command=copy_to_clipboard, cursor="hand2")
        copy_label.grid(row=0, column=0, pady=5, padx=5, sticky='w')
        copy_label.bind("<Button-1>", copy_to_clipboard)
        result_text.bind("<Button-3>", copy_to_clipboard)
        
    

    # เพิ่มปุ่ม "View History"
        history_btn = ttk.Button(result_frame_r2, text="⏳ View More and History", command=show_history)
        history_btn.grid(row=1, column=0,columnspan=2, padx=5, pady=5, sticky='we')
    
        return total_volume_change, reset_gui
    
    def plot_graph(src_avg_alt_mat, tgt_avg_alt_mat, delta_alt_mat, gbl_z_min, gbl_z_max, width_meters, height_meters, sand_increase, sand_decrease):
        norm = Normalize(vmin=gbl_z_min, vmax=gbl_z_max)
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        axes[1, 1].axis('off')
    # Subplot 1: Average Altitude (Source)
        im1 = axes[0, 0].imshow(src_avg_alt_mat, cmap='viridis_r', norm=norm)
        axes[0, 0].set_title('Average Altitude (Time Series1)')
        axes[0, 0].set_xlabel(f'Width {width_meters:.2f} meters')
        axes[0, 0].set_ylabel(f'Height {height_meters:.2f} meters')
        axes[0, 0].invert_yaxis()

    # Subplot 2: Average Altitude (Target)
        im2 = axes[0, 1].imshow(tgt_avg_alt_mat, cmap='viridis_r', norm=norm)
        axes[0, 1].set_title('Average Altitude (Time Series2)')
        axes[0, 1].set_xlabel(f'Width {width_meters:.2f} meters')
        axes[0, 1].set_ylabel(f'Height {height_meters:.2f} meters')
        axes[0, 1].invert_yaxis()

    # Subplot 3: Delta Altitude (Volume Change)
        im3 = axes[1, 0].imshow(delta_alt_mat, cmap='viridis_r', norm=norm)
        axes[1, 0].set_title('Delta Altitude (Volume Change)')
        axes[1, 0].set_xlabel(f'Width {width_meters:.2f} meters')
        axes[1, 0].set_ylabel(f'Height {height_meters:.2f} meters')
        axes[1, 0].invert_yaxis()

    # Subplot 4: Period of change
        threshold_min = -0.1
        threshold_max = 0.1
        norm1 = Normalize(vmin=threshold_min, vmax=threshold_max)
        im4 = axes[1, 1].imshow(delta_alt_mat, cmap='bwr', norm=norm1)
        axes[1, 1].set_title('Period of change')
        axes[1, 1].set_xlabel('Width (meters)')
        axes[1, 1].set_ylabel('Height (meters)')
        axes[1, 1].invert_yaxis()
        axes[1, 1].text(0.5, -0.15, f'> 0.1 m : Sand Increase(Red)\n< -0.1 m : Sand Decrease(Blue)\n Sand Volume Increase: {sand_increase:.2f} m³\nSand Volume Decrease: {sand_decrease:.2f} m³',
            fontsize=12, ha='center', va='top', transform=axes[1, 1].transAxes)

    # Add colorbars for each graph
        fig.colorbar(im1, ax=axes[0, 0])
        fig.colorbar(im2, ax=axes[0, 1])
        fig.colorbar(im3, ax=axes[1, 0])
        fig.colorbar(im4, ax=axes[1, 1])

        plt.tight_layout()
        plt.show()
    
    def start_progress(stop_animation,progress_queue):
        progress_bar.grid()
        def update_progress():
            if not progress_queue.empty():
                percentage = progress_queue.get()
                progress_bar['value'] = percentage
            if not stop_animation.is_set():  
                root.after(100, update_progress)  # อัปเดตทุก 100ms
            else:
                progress_bar["value"] = 100
                progress_bar.grid_remove()

        update_progress()
    

    if pcd1 != None and pcd2 != None:
        start_calculate_btn.state(['!disabled'])  # ปิดการใช้งานปุ่มเริ่มคำนวณ
        
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    
    
    # try:
    #     dolphin_gif = Image.open('./blankspace/image/gif2.gif')  # ใส่พาธ GIF ของคุณ
    # except:
    #     dolphin_gif = Image.open('./image/gif2.gif')  # ใส่พาธ GIF ของคุณ
    # dolphin_sequence = [
    #     ImageTk.PhotoImage(img.resize((50, 70), Image.Resampling.LANCZOS))
    #     for img in ImageSequence.Iterator(dolphin_gif)
    # ]
    
    stop_animation = threading.Event() 

    root.mainloop()

def show_matrix(matrix):
    matrix_str = np.array2string(matrix, formatter={'float_kind': lambda x: f'{x:.2f}'})
    messagebox.showinfo("Transformation Matrix", matrix_str)

def visualize_a_point_cloud(pcd, title):
    try:
        # o3d.visualization.draw_geometries([pcd], window_name=title)
        temp_file = f"{title}.ply"
        o3d.io.write_point_cloud(temp_file, pcd)

        subprocess.Popen(["python", "visualize.py", temp_file, title], start_new_session=True)
        # visualize_exe_path = os.path.join(os.path.dirname(__file__), "visualize.exe")
        # visualize_exe_path = r'D:\blankspace\meen\SeaDan_BlankSpace\visualize.exe'
        # subprocess.Popen([visualize_exe_path, temp_file, title])
        
    except:
        messagebox.showwarning("Error", "กรุณาเลือกไฟล์ LAS ก่อน")

def start_viewer(pcd1, pcd2, step):
    if pcd1 is not None and pcd2 is not None:
        def run_viewer():
            matrix1 = np.eye(4)
            matrix2 = np.eye(4)
            translation_offset = np.array([-0.1,0.0,0.0])  
            pcd1.translate(translation_offset)
            draw_interactive(pcd1, pcd2, matrix1, matrix2, step)
        # threading.Thread(target=run_viewer, daemon=True).start
        run_viewer()
    else:
        messagebox.showerror("Error", "Please load both files before starting the viewer.")

def show_man():
    data_man = {
        'key_shortcut': ['A', 'D', 'W', 'S', 'X', 'Y', 'Z', 'Q', 'E'],
        'description': ['Move point cloud to the left', 
                        'Move point cloud to the right', 
                        'Move point cloud forward', 
                        'Move point cloud backward', 
                        'Rotate the point cloud along the X axis.', 
                        'Rotate the point cloud along the Y axis.', 
                        'Rotate the point cloud along the Z axis.', 
                        'Move pointcloud upper',
                        'Move pointcloud lower']
    }
    
    table_window = tk.Toplevel()
    table_window.geometry("400x250")
    table_window.title('Key button')
    table_window.configure(bg="#F1AA9B")
    
    columns = ('Key Shortcut', 'Description')
    tree = ttk.Treeview(table_window, columns=columns, show='headings')
    
    tree.heading('Key Shortcut', text='Key Shortcut') 
    tree.column('Key Shortcut', width=80, anchor='center')
        
    tree.heading('Description', text='Description')
    tree.column('Description', width=200, anchor='w')
    
    keys = data_man['key_shortcut']
    descriptions = data_man['description']
    
    for i in range(len(keys)):
        tree.insert('', 'end', values=(keys[i], descriptions[i]))
    
    tree.pack(expand=True, fill='both', padx=10, pady=10)

def draw_interactive(pcd1, pcd2, matrix1, matrix2, step):
    vis = o3d.visualization.VisualizerWithKeyCallback()
    try:
        vis.create_window()
        vis.add_geometry(pcd1)
        vis.add_geometry(pcd2)
        key_callback_1(vis, pcd2, matrix2, step)
        vis.run()
    finally:
        vis.destroy_window()

def run_merge_cut_script():
    # ดึง path ปัจจุบันของไฟล์ SeaDanFlow_dev0.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # script_path = os.path.join(script_dir, "automate_manage_mem.py")
    script_path = os.path.join(script_dir, "merge_and_cut.py")   

    try:
        subprocess.Popen([sys.executable, script_path])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch Merge & Cut: {e}")


if __name__ == "__main__":
    create_gui()