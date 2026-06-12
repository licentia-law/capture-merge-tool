import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageGrab
import os

class CaptureMergeApp:
    PREVIEW_VERTICAL_WIDTH = 550
    PREVIEW_HORIZONTAL_HEIGHT = 550

    def __init__(self, root):
        self.root = root
        self.root.title("캡쳐 병합 도구 (자동 수집)")
        self.root.geometry("600x800")
        
        # 설정
        self.images = []
        self.initial_status_text = "클립보드 모니터링 시작!\n(Win+Shift+S 등으로 캡쳐 시 자동 추가)"
        self.preview_images = []
        self.merge_direction = tk.StringVar(value="vertical")
        self.last_img_bytes = None
        
        # UI 구성 - 상단 프레임
        self.top_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(self.top_frame, text=self.initial_status_text, fg="#333333", bg="#f0f0f0", justify=tk.LEFT)
        self.status_label.pack(side=tk.LEFT)
        
        self.btn_save = tk.Button(self.top_frame, text="완료 및 저장", command=self.save_merged, bg="#4CAF50", fg="white", font=("맑은 고딕", 11, "bold"), padx=10, pady=5)
        self.btn_save.pack(side=tk.RIGHT)

        self.btn_reset = tk.Button(self.top_frame, text="초기화", command=self.reset_images, bg="#757575", fg="white", font=("맑은 고딕", 11, "bold"), padx=10, pady=5)
        self.btn_reset.pack(side=tk.RIGHT, padx=(0, 10))

        self.direction_frame = tk.Frame(self.top_frame, bg="#f0f0f0")
        self.direction_frame.pack(side=tk.RIGHT, padx=(0, 10))

        self.btn_vertical = tk.Radiobutton(
            self.direction_frame,
            text="세로",
            variable=self.merge_direction,
            value="vertical",
            command=self.refresh_preview,
            bg="#f0f0f0",
            font=("맑은 고딕", 10),
        )
        self.btn_vertical.pack(side=tk.LEFT)

        self.btn_horizontal = tk.Radiobutton(
            self.direction_frame,
            text="가로",
            variable=self.merge_direction,
            value="horizontal",
            command=self.refresh_preview,
            bg="#f0f0f0",
            font=("맑은 고딕", 10),
        )
        self.btn_horizontal.pack(side=tk.LEFT)
        
        # UI 구성 - 캔버스 (스크롤 가능)
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#e0e0e0")
        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg="#e0e0e0")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        # 마우스 휠 스크롤 연동
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.preview_widgets = []
        
        # 앱 시작시 기존 클립보드 비우기 (불필요한 이전 복사 이미지 방지)
        self.clear_clipboard()
        
        # 주기적 클립보드 확인 시작
        self.check_clipboard()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def clear_clipboard(self):
        try:
            import ctypes
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            ctypes.windll.user32.CloseClipboard()
        except:
            pass
            
    def check_clipboard(self):
        try:
            # 클립보드에서 이미지 가져오기
            img = ImageGrab.grabclipboard()
            
            # 클립보드 내용이 이미지인지 확인
            if isinstance(img, Image.Image):
                img_bytes = img.tobytes()
                # 마지막에 복사된 이미지와 다를 경우에만 추가
                if self.last_img_bytes != img_bytes:
                    self.last_img_bytes = img_bytes
                    self.add_image(img)
        except Exception:
            pass
        
        # 0.5초(500ms)마다 다시 확인 반복
        self.root.after(500, self.check_clipboard)
        
    def make_preview_image(self, img):
        if self.merge_direction.get() == "horizontal":
            ratio = self.PREVIEW_HORIZONTAL_HEIGHT / float(img.height)
            display_width = int((float(img.width) * float(ratio)))
            display_height = self.PREVIEW_HORIZONTAL_HEIGHT
        else:
            display_width = self.PREVIEW_VERTICAL_WIDTH
            ratio = display_width / float(img.width)
            display_height = int((float(img.height) * float(ratio)))

        return img.resize((display_width, display_height), Image.Resampling.LANCZOS)

    def update_status(self):
        if self.images:
            self.status_label.config(text=f"캡쳐 자동 수집 중...\n현재 누적: {len(self.images)}장", fg="blue")
        else:
            self.status_label.config(text=self.initial_status_text, fg="#333333")

    def refresh_preview(self):
        for widget in self.preview_widgets:
            widget.destroy()
        self.preview_widgets.clear()
        self.preview_images.clear()

        horizontal = self.merge_direction.get() == "horizontal"
        for index, img in enumerate(self.images):
            display_img = self.make_preview_image(img)
            photo = ImageTk.PhotoImage(display_img)

            item_frame = tk.Frame(self.scrollable_frame, bg="#e0e0e0")
            if horizontal:
                item_frame.pack(side=tk.LEFT, pady=10, padx=10)
            else:
                item_frame.pack(side=tk.TOP, pady=10, padx=10)

            delete_btn = tk.Button(
                item_frame,
                text="삭제",
                command=lambda idx=index: self.delete_image(idx),
                bg="#d9534f",
                fg="white",
                font=("맑은 고딕", 9, "bold"),
                padx=8,
                pady=2,
            )
            delete_btn.pack(side=tk.TOP, anchor=tk.E, pady=(0, 4))

            lbl = tk.Label(item_frame, image=photo, bg="white", borderwidth=2, relief="groove")
            lbl.image = photo
            lbl.pack(side=tk.TOP)

            self.preview_widgets.append(item_frame)
            self.preview_images.append(photo)

        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if horizontal:
            self.canvas.xview_moveto(1.0)
        else:
            self.canvas.yview_moveto(1.0)

    def add_image(self, img):
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        self.images.append(img)
        self.refresh_preview()
        self.update_status()

    def delete_image(self, index):
        if 0 <= index < len(self.images):
            del self.images[index]
            self.refresh_preview()
            self.update_status()

    def reset_images(self, confirm=True):
        if confirm and self.images:
            confirmed = messagebox.askyesno("초기화", "현재 수집된 캡쳐 이미지를 모두 삭제하시겠습니까?")
            if not confirmed:
                return

        self.images.clear()
        self.last_img_bytes = None
        self.refresh_preview()
        self.update_status()
        self.clear_clipboard()
        
    def save_merged(self):
        if not self.images:
            messagebox.showwarning("경고", "캡쳐된 이미지가 하나도 없습니다.\n캡쳐를 먼저 진행해주세요.")
            return
            
        save_folder = filedialog.askdirectory(title="결과물을 저장할 폴더를 선택하세요")
        if not save_folder:
            return
            
        try:
            if self.merge_direction.get() == "horizontal":
                total_width = sum(img.width for img in self.images)
                max_height = max(img.height for img in self.images)

                # 최종 병합 이미지 (원본 사이즈, 무손실)
                merged_image = Image.new('RGB', (total_width, max_height), color=(255, 255, 255))

                x_offset = 0
                for img in self.images:
                    merged_image.paste(img, (x_offset, 0))
                    x_offset += img.width
            else:
                max_width = max(img.width for img in self.images)
                total_height = sum(img.height for img in self.images)

                # 최종 병합 이미지 (원본 사이즈, 무손실)
                merged_image = Image.new('RGB', (max_width, total_height), color=(255, 255, 255))

                y_offset = 0
                for img in self.images:
                    merged_image.paste(img, (0, y_offset))
                    y_offset += img.height
                
            output_path = os.path.join(save_folder, "capture_merged.png")
            merged_image.save(output_path, format="PNG", quality=100)
            
            messagebox.showinfo("완료", f"총 {len(self.images)}장의 캡쳐 이미지가 한 장으로 병합되었습니다!\n\n저장 경로:\n{output_path}")
            self.reset_images(confirm=False)
        except Exception as e:
            messagebox.showerror("오류", f"이미지 통합 중 문제가 발생했습니다.\n{e}")

def main():
    root = tk.Tk()
    app = CaptureMergeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
