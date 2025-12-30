
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import os
import threading
import sys
import shutil

# 设置外观模式 (System, Dark, Light)
ctk.set_appearance_mode("System")  
# 设置默认颜色主题 (blue, dark-blue, green)
ctk.set_default_color_theme("blue")

class WatermarkRemoverApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 窗口基本配置 ---
        self.title("NotebookLM PDF 水印去除助手")
        self.geometry("700x550")
        
        # --- 核心数据 ---
        self.selected_path = ""
        self.is_debugging = False
        
        # --- 布局配置 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Title
        self.grid_rowconfigure(1, weight=0) # Input
        self.grid_rowconfigure(2, weight=0) # Settings
        self.grid_rowconfigure(3, weight=0) # Progress
        self.grid_rowconfigure(4, weight=1) # Log

        # 1. 标题
        self.lbl_title = ctk.CTkLabel(self, text="PDF 智能去除水印工具", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 2. 文件选择区域
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry_path = ctk.CTkEntry(self.input_frame, placeholder_text="请选择 PDF 文件或包含 PDF 的文件夹...")
        self.entry_path.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.btn_browse_file = ctk.CTkButton(self.input_frame, text="选择文件", command=self.browse_file, width=100)
        self.btn_browse_file.grid(row=0, column=1, padx=5, pady=10)
        
        self.btn_browse_folder = ctk.CTkButton(self.input_frame, text="选择文件夹", command=self.browse_folder, width=100)
        self.btn_browse_folder.grid(row=0, column=2, padx=(5, 10), pady=10)

        # 3. 参数配置区域 (高级设置)
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_settings = ctk.CTkLabel(self.settings_frame, text="参数调整 (像素)", font=ctk.CTkFont(weight="bold"))
        self.lbl_settings.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # 宽度
        self.lbl_w = ctk.CTkLabel(self.settings_frame, text="覆盖宽度:")
        self.lbl_w.grid(row=1, column=0, padx=(10, 5), pady=5)
        self.entry_w = ctk.CTkEntry(self.settings_frame, width=60)
        self.entry_w.insert(0, "120") # 默认值，来自用户之前的调整
        self.entry_w.grid(row=1, column=1, padx=5, pady=5)
        
        # 高度
        self.lbl_h = ctk.CTkLabel(self.settings_frame, text="覆盖高度:")
        self.lbl_h.grid(row=1, column=2, padx=(10, 5), pady=5)
        self.entry_h = ctk.CTkEntry(self.settings_frame, width=60)
        self.entry_h.insert(0, "30") # 默认值，来自用户之前的调整
        self.entry_h.grid(row=1, column=3, padx=5, pady=5)
        
        # 调试模式开关
        self.chk_debug = ctk.CTkCheckBox(self.settings_frame, text="调试模式 (显示红框)", command=self.toggle_debug)
        self.chk_debug.grid(row=1, column=4, padx=20, pady=5)
        
        # 开始按钮
        self.btn_start = ctk.CTkButton(self.settings_frame, text="开始处理", command=self.start_processing_thread, fg_color="green", hover_color="darkgreen", height=40)
        self.btn_start.grid(row=1, column=5, padx=20, pady=10, sticky="e")

        # 4. 进度条
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.progress_bar.set(0)

        # 5. 日志控制区域
        self.log_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.log_frame.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.lbl_log = ctk.CTkLabel(self.log_frame, text="执行日志", font=ctk.CTkFont(weight="bold"))
        self.lbl_log.pack(side="left")
        
        self.btn_clear_log = ctk.CTkButton(self.log_frame, text="清除日志", command=self.clear_log, width=80, height=24)
        self.btn_clear_log.pack(side="right")

        # 6. 日志输出文本框
        self.textbox_log = ctk.CTkTextbox(self, width=650)
        self.textbox_log.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        self.log("就绪。请选择文件或文件夹开始。")

    def toggle_debug(self):
        self.is_debugging = self.chk_debug.get()

    def log(self, message):
        self.textbox_log.insert("end", message + "\n")
        self.textbox_log.see("end")

    def clear_log(self):
        self.textbox_log.delete("1.0", "end")

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.selected_path = filename
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, filename)

    def browse_folder(self):
        foldername = filedialog.askdirectory()
        if foldername:
            self.selected_path = foldername
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, foldername)

    def start_processing_thread(self):
        path = self.entry_path.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("错误", "请输入有效的文件或文件夹路径。")
            return
            
        # 获取参数
        try:
            w = int(self.entry_w.get())
            h = int(self.entry_h.get())
        except ValueError:
            messagebox.showerror("错误", "宽度和高度必须是整数。")
            return

        # 禁用按钮防止重复点击
        self.btn_start.configure(state="disabled")
        self.progress_bar.set(0)
        
        # 开启线程
        thread = threading.Thread(target=self.process_logic, args=(path, w, h))
        thread.start()

    def process_logic(self, path, rect_width, rect_height):
        files_to_process = []
        output_base_dir = "" # 统一的输出目录

        if os.path.isfile(path):
            if path.lower().endswith(".pdf"):
                files_to_process.append(path)
                # 单个文件模式：输出目录在文件同级下的 "去水印" 文件夹
                output_base_dir = os.path.join(os.path.dirname(path), "去水印")
                
        elif os.path.isdir(path):
            # 文件夹模式：只扫描当前目录，不包含子目录
            output_base_dir = os.path.join(path, "去水印")
            try:
                for file in os.listdir(path):
                    full_path = os.path.join(path, file)
                    if os.path.isfile(full_path) and file.lower().endswith(".pdf"):
                        files_to_process.append(full_path)
            except Exception as e:
                self.log(f"扫描目录出错: {e}")

        total_files = len(files_to_process)
        if total_files == 0:
            self.log("未找到 PDF 文件。")
            self.btn_start.configure(state="normal")
            return

        # 创建输出目录
        if not os.path.exists(output_base_dir):
            try:
                os.makedirs(output_base_dir)
            except Exception as e:
                self.log(f"创建输出目录失败: {e}")
                self.btn_start.configure(state="normal")
                return

        self.log(f"找到 {total_files} 个 PDF 文件，准备处理...")
        self.log(f"输出目录: {output_base_dir}")
        
        success_count = 0
        
        for idx, file_path in enumerate(files_to_process):
            filename = os.path.basename(file_path)
            self.log(f"[{idx+1}/{total_files}] 正在处理: {filename}")
            
            try:
                # 统一输出到 simple 去水印 folder
                output_path = os.path.join(output_base_dir, filename)
                
                # 调用核心处理逻辑
                self.remove_watermark_core(file_path, output_path, rect_width, rect_height)
                
                success_count += 1
                self.log(f"    -> 完成")
                
            except Exception as e:
                self.log(f"    -> 失败: {str(e)}")
            
            # 更新进度条
            progress = (idx + 1) / total_files
            self.progress_bar.set(progress)
        
        self.log("\n======================")
        self.log(f"全部任务完成！成功 {success_count}/{total_files} 个。")
        self.btn_start.configure(state="normal")
        messagebox.showinfo("完成", f"处理完成！\n成功: {success_count}\n失败: {total_files - success_count}\n位置: {output_base_dir}")

    def remove_watermark_core(self, input_pdf, output_pdf, rect_w, rect_h):
        """核心去除水印逻辑"""
        doc = fitz.open(input_pdf)
        
        # 硬编码的边距默认值 (或者也可以添加到界面)
        margin_right = 0
        margin_bottom = 0
        debug = self.chk_debug.get()

        for page in doc:
            page_width = page.rect.width
            page_height = page.rect.height
            
            x0 = page_width - rect_w - margin_right
            y0 = page_height - rect_h - margin_bottom
            x1 = page_width - margin_right
            y1 = page_height - margin_bottom
            
            rect = fitz.Rect(x0, y0, x1, y1)
            
            # 吸色逻辑
            probe_point = fitz.Point(x0 - 5, y1 - 5)
            if probe_point.x < 0: probe_point.x = 0
            if probe_point.y < 0: probe_point.y = 0
            
            clip_rect = fitz.Rect(probe_point.x, probe_point.y, probe_point.x+1, probe_point.y+1)
            pix = page.get_pixmap(clip=clip_rect)
            
            if len(pix.samples) >= 3:
                r = pix.samples[0]
                g = pix.samples[1]
                b = pix.samples[2]
                color = (r/255.0, g/255.0, b/255.0)
            else:
                color = (1, 1, 1) # White backup
            
            shape = page.new_shape()
            shape.draw_rect(rect)
            
            if debug:
                shape.finish(fill=color, color=(1, 0, 0), width=2) # Red border
            else:
                shape.finish(fill=color, color=color) # Invisible border
                
            shape.commit()
            
        doc.save(output_pdf)
        doc.close()

if __name__ == "__main__":
    app = WatermarkRemoverApp()
    app.mainloop()
