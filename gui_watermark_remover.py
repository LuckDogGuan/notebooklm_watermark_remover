
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

# Language dictionary
LANGUAGES = {
    "zh": {
        "title": "PDF 智能去除水印工具",
        "window_title": "NotebookLM PDF 水印去除助手",
        "placeholder": "请选择 PDF 文件或包含 PDF 的文件夹...",
        "select_file": "选择文件",
        "select_folder": "选择文件夹",
        "settings": "参数调整 (像素)",
        "width": "覆盖宽度:",
        "height": "覆盖高度:",
        "debug_mode": "调试模式 (显示红框)",
        "start": "开始处理",
        "log_title": "执行日志",
        "clear_log": "清除日志",
        "ready": "就绪。请选择文件或文件夹开始。",
        "error": "错误",
        "invalid_path": "请输入有效的文件或文件夹路径。",
        "invalid_number": "宽度和高度必须是整数。",
        "no_files": "未找到 PDF 文件。",
        "scan_error": "扫描目录出错: {}",
        "create_dir_error": "创建输出目录失败: {}",
        "found_files": "找到 {} 个 PDF 文件，准备处理...",
        "output_dir": "输出目录: {}",
        "processing": "[{}/{}] 正在处理: {}",
        "complete": "    -> 完成",
        "failed": "    -> 失败: {}",
        "all_done": "全部任务完成！成功 {}/{} 个。",
        "done_title": "完成",
        "done_msg": "处理完成！\n成功: {}\n失败: {}\n位置: {}",
        "language": "Language"
    },
    "en": {
        "title": "PDF Watermark Remover",
        "window_title": "NotebookLM PDF Watermark Remover",
        "placeholder": "Select PDF file or folder containing PDFs...",
        "select_file": "Select File",
        "select_folder": "Select Folder",
        "settings": "Settings (pixels)",
        "width": "Width:",
        "height": "Height:",
        "debug_mode": "Debug Mode (Show Red Box)",
        "start": "Start Processing",
        "log_title": "Log",
        "clear_log": "Clear Log",
        "ready": "Ready. Please select a file or folder to start.",
        "error": "Error",
        "invalid_path": "Please enter a valid file or folder path.",
        "invalid_number": "Width and height must be integers.",
        "no_files": "No PDF files found.",
        "scan_error": "Error scanning directory: {}",
        "create_dir_error": "Failed to create output directory: {}",
        "found_files": "Found {} PDF files, preparing to process...",
        "output_dir": "Output directory: {}",
        "processing": "[{}/{}] Processing: {}",
        "complete": "    -> Complete",
        "failed": "    -> Failed: {}",
        "all_done": "All tasks completed! Success {}/{}.",
        "done_title": "Complete",
        "done_msg": "Processing complete!\nSuccess: {}\nFailed: {}\nLocation: {}",
        "language": "语言"
    }
}

class WatermarkRemoverApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 核心数据 ---
        self.selected_path = ""
        self.is_debugging = False
        self.current_lang = "zh"  # Default language
        
        # --- 窗口基本配置 ---
        self.title(self.t("window_title"))
        self.geometry("700x580")
        
        # --- 布局配置 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Title
        self.grid_rowconfigure(1, weight=0) # Language
        self.grid_rowconfigure(2, weight=0) # Input
        self.grid_rowconfigure(3, weight=0) # Settings
        self.grid_rowconfigure(4, weight=0) # Progress
        self.grid_rowconfigure(5, weight=0) # Log control
        self.grid_rowconfigure(6, weight=1) # Log

        # 1. 标题
        self.lbl_title = ctk.CTkLabel(self, text=self.t("title"), font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # 2. 语言切换
        self.lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.lang_frame.grid(row=1, column=0, padx=20, pady=5, sticky="e")
        
        self.lbl_lang = ctk.CTkLabel(self.lang_frame, text=self.t("language") + ":", font=ctk.CTkFont(size=12))
        self.lbl_lang.pack(side="left", padx=5)
        
        self.lang_switch = ctk.CTkSegmentedButton(self.lang_frame, values=["中文", "English"], command=self.switch_language)
        self.lang_switch.set("中文")
        self.lang_switch.pack(side="left")

        # 3. 文件选择区域
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry_path = ctk.CTkEntry(self.input_frame, placeholder_text=self.t("placeholder"))
        self.entry_path.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.btn_browse_file = ctk.CTkButton(self.input_frame, text=self.t("select_file"), command=self.browse_file, width=100)
        self.btn_browse_file.grid(row=0, column=1, padx=5, pady=10)
        
        self.btn_browse_folder = ctk.CTkButton(self.input_frame, text=self.t("select_folder"), command=self.browse_folder, width=100)
        self.btn_browse_folder.grid(row=0, column=2, padx=(5, 10), pady=10)

        # 4. 参数配置区域 (高级设置)
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_settings = ctk.CTkLabel(self.settings_frame, text=self.t("settings"), font=ctk.CTkFont(weight="bold"))
        self.lbl_settings.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # 宽度
        self.lbl_w = ctk.CTkLabel(self.settings_frame, text=self.t("width"))
        self.lbl_w.grid(row=1, column=0, padx=(10, 5), pady=5)
        self.entry_w = ctk.CTkEntry(self.settings_frame, width=60)
        self.entry_w.insert(0, "120") # 默认值，来自用户之前的调整
        self.entry_w.grid(row=1, column=1, padx=5, pady=5)
        
        # 高度
        self.lbl_h = ctk.CTkLabel(self.settings_frame, text=self.t("height"))
        self.lbl_h.grid(row=1, column=2, padx=(10, 5), pady=5)
        self.entry_h = ctk.CTkEntry(self.settings_frame, width=60)
        self.entry_h.insert(0, "30") # 默认值，来自用户之前的调整
        self.entry_h.grid(row=1, column=3, padx=5, pady=5)
        
        # 调试模式开关
        self.chk_debug = ctk.CTkCheckBox(self.settings_frame, text=self.t("debug_mode"), command=self.toggle_debug)
        self.chk_debug.grid(row=1, column=4, padx=20, pady=5)
        
        # 开始按钮
        self.btn_start = ctk.CTkButton(self.settings_frame, text=self.t("start"), command=self.start_processing_thread, fg_color="green", hover_color="darkgreen", height=40)
        self.btn_start.grid(row=1, column=5, padx=20, pady=10, sticky="e")

        # 5. 进度条
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.progress_bar.set(0)

        # 6. 日志控制区域
        self.log_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.log_frame.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.lbl_log = ctk.CTkLabel(self.log_frame, text=self.t("log_title"), font=ctk.CTkFont(weight="bold"))
        self.lbl_log.pack(side="left")
        
        self.btn_clear_log = ctk.CTkButton(self.log_frame, text=self.t("clear_log"), command=self.clear_log, width=80, height=24)
        self.btn_clear_log.pack(side="right")

        # 7. 日志输出文本框
        self.textbox_log = ctk.CTkTextbox(self, width=650)
        self.textbox_log.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")
        self.log(self.t("ready"))

    def t(self, key):
        """Get translation for current language"""
        return LANGUAGES[self.current_lang].get(key, key)
    
    def switch_language(self, value):
        """Switch between Chinese and English"""
        self.current_lang = "zh" if value == "中文" else "en"
        self.update_ui_text()
        # Clear log and show ready message in new language
        self.clear_log()
        self.log(self.t("ready"))
    
    def update_ui_text(self):
        """Update all UI text elements"""
        self.title(self.t("window_title"))
        self.lbl_title.configure(text=self.t("title"))
        self.lbl_lang.configure(text=self.t("language") + ":")
        self.entry_path.configure(placeholder_text=self.t("placeholder"))
        self.btn_browse_file.configure(text=self.t("select_file"))
        self.btn_browse_folder.configure(text=self.t("select_folder"))
        self.lbl_settings.configure(text=self.t("settings"))
        self.lbl_w.configure(text=self.t("width"))
        self.lbl_h.configure(text=self.t("height"))
        self.chk_debug.configure(text=self.t("debug_mode"))
        self.btn_start.configure(text=self.t("start"))
        self.lbl_log.configure(text=self.t("log_title"))
        self.btn_clear_log.configure(text=self.t("clear_log"))

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
            messagebox.showerror(self.t("error"), self.t("invalid_path"))
            return
            
        # 获取参数
        try:
            w = int(self.entry_w.get())
            h = int(self.entry_h.get())
        except ValueError:
            messagebox.showerror(self.t("error"), self.t("invalid_number"))
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
                self.log(self.t("scan_error").format(e))

        total_files = len(files_to_process)
        if total_files == 0:
            self.log(self.t("no_files"))
            self.btn_start.configure(state="normal")
            return

        # 创建输出目录
        if not os.path.exists(output_base_dir):
            try:
                os.makedirs(output_base_dir)
            except Exception as e:
                self.log(self.t("create_dir_error").format(e))
                self.btn_start.configure(state="normal")
                return

        self.log(self.t("found_files").format(total_files))
        self.log(self.t("output_dir").format(output_base_dir))
        
        success_count = 0
        
        for idx, file_path in enumerate(files_to_process):
            filename = os.path.basename(file_path)
            self.log(self.t("processing").format(idx+1, total_files, filename))
            
            try:
                # 统一输出到 simple 去水印 folder
                output_path = os.path.join(output_base_dir, filename)
                
                # 调用核心处理逻辑
                self.remove_watermark_core(file_path, output_path, rect_width, rect_height)
                
                success_count += 1
                self.log(self.t("complete"))
                
            except Exception as e:
                self.log(self.t("failed").format(str(e)))
            
            # 更新进度条
            progress = (idx + 1) / total_files
            self.progress_bar.set(progress)
        
        self.log("\n======================")
        self.log(self.t("all_done").format(success_count, total_files))
        self.btn_start.configure(state="normal")
        messagebox.showinfo(self.t("done_title"), self.t("done_msg").format(success_count, total_files - success_count, output_base_dir))

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
