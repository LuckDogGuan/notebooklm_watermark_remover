
import fitz
import sys

def cover_watermark(input_pdf, output_pdf):
    print(f"Opening {input_pdf}...")
    doc = fitz.open(input_pdf)
    
    # 默认水印位置配置 (根据经验值，可根据实际效果微调)
    # 假设水印在右下角
    # 注意：PDF 坐标系有点复杂，PyMuPDF 中 (0,0) 通常是左上角
    
    # ==========================================
    # [用户配置区域] 请根据实际情况调整以下数值
    # ==========================================
    # 水印覆盖框的尺寸 (单位：像素)
    # 如果遮不住，可以把这两个值改大一点
    RECT_WIDTH = 120   # 覆盖框宽度
    RECT_HEIGHT = 30   # 覆盖框高度
    
    # 水印距离边缘的距离 (单位：像素)
    # (0,0) 代表紧贴着右下角
    MARGIN_RIGHT = 0   # 距离右边框的距离
    MARGIN_BOTTOM = 0  # 距离底部的距离
    
    # 调试模式：True = 显示红色边框，False = 隐藏边框 (正式导出时改为 False)
    DEBUG_MODE = True
    # ==========================================
    
    total_pages = len(doc)
    print(f"Total pages to process: {total_pages}")

    for page_num, page in enumerate(doc):
        # 获取当前页面的宽和高 (自适应页面大小)
        page_width = page.rect.width
        page_height = page.rect.height
        
        # 动态计算覆盖框的坐标 (锚点在右下角)
        # 无论页面多大，都始终定位在右下角
        x0 = page_width - RECT_WIDTH - MARGIN_RIGHT
        y0 = page_height - RECT_HEIGHT - MARGIN_BOTTOM
        x1 = page_width - MARGIN_RIGHT
        y1 = page_height - MARGIN_BOTTOM
        
        # 定义矩形区域
        rect = fitz.Rect(x0, y0, x1, y1)
        
        # --- 自动吸取背景色 ---
        # 我们取矩形左上角稍微往外一点点的像素作为背景色参考
        # 即使 PDF 是纯图片，我们也可以渲染这一小块区域来取色
        
        # 截取一个小样本区域 (probe)
        probe_point = fitz.Point(x0 - 5, y1 - 5) # 采样点：水印框左边一点的位置
        
        # 如果采样点超出范围，就取其他位置，这里做个简单保护
        if probe_point.x < 0: probe_point.x = 0
        
        # 渲染页面成像素图来取色 (只渲染一小块以提速)
        clip_rect = fitz.Rect(probe_point.x, probe_point.y, probe_point.x+1, probe_point.y+1)
        pix = page.get_pixmap(clip=clip_rect)
        
        # 获取像素值 (R, G, B)
        # pix.samples 是字节流
        if len(pix.samples) >= 3:
            r = pix.samples[0]
            g = pix.samples[1]
            b = pix.samples[2]
            color = (r/255.0, g/255.0, b/255.0) # PyMuPDF 要求 0-1 浮点数
        else:
            # 默认白色
            color = (1, 1, 1)
            
        print(f"Page {page_num+1}: Detected background color RGB({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)})")

        # --- 绘制覆盖层 ---
        shape = page.new_shape()
        shape.draw_rect(rect)
        
        if DEBUG_MODE:
            # 调试模式：红色边框，线宽 2
            shape.finish(fill=color, color=(1, 0, 0), width=2)
        else:
            # 正常模式：边框颜色与填充颜色一致，看起来就是无边框
            shape.finish(fill=color, color=color) 
            
        shape.commit()

    doc.save(output_pdf)
    print(f"Saved processed file to {output_pdf}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_cover_watermark.py <input_pdf>")
    else:
        cover_watermark(sys.argv[1], "covered_output.pdf")
