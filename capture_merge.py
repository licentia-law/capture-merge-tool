import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageGrab
import os

class CaptureMergeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("캡쳐 병합 도구 (자동 수집)")
        self.root.geometry("600x800")
        
        # 설정
        self.images = []
        self.last_img_bytes = None
        
        # UI 구성 - 상단 프레임
        self.top_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(self.top_frame, text="클립보드 모니터링 시작!\n(Win+Shift+S 등으로 캡쳐 시 자동 추가)", fg="#333333", bg="#f0f0f0", justify=tk.LEFT)
        self.status_label.pack(side=tk.LEFT)
        
        self.btn_save = tk.Button(self.top_frame, text="완료 및 저장", command=self.save_and_exit, bg="#4CAF50", fg="white", font=("맑은 고딕", 11, "bold"), padx=10, pady=5)
        self.btn_save.pack(side=tk.RIGHT)
        
        # UI 구성 - 캔버스 (스크롤 가능)
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#e0e0e0")
        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
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
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.image_labels = []
        
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
        
    def add_image(self, img):
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        self.images.append(img)
        
        # 앱 화면에 보일 수 있게 가로 550px 비율에 맞게 리사이징
        display_width = 550
        ratio = display_width / float(img.width)
        display_height = int((float(img.height) * float(ratio)))
        display_img = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(display_img)
        
        lbl = tk.Label(self.scrollable_frame, image=photo, bg="white", borderwidth=2, relief="groove")
        lbl.image = photo  # 참조 유지 필요
        lbl.pack(pady=10, padx=10)
        self.image_labels.append(lbl)
        
        self.status_label.config(text=f"캡쳐 자동 수집 중...\n현재 누적: {len(self.images)}장", fg="blue")
        
        # 이미지가 추가되면 스크롤을 맨 아래로 이동
        self.root.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
    def save_and_exit(self):
        if not self.images:
            messagebox.showwarning("경고", "캡쳐된 이미지가 하나도 없습니다.\n캡쳐를 먼저 진행해주세요.")
            return
            
        save_folder = filedialog.askdirectory(title="결과물을 저장할 폴더를 선택하세요")
        if not save_folder:
            return
            
        try:
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
            
            # 완료 후 프로그램 종료
            self.root.quit()
        except Exception as e:
            messagebox.showerror("오류", f"이미지 통합 중 문제가 발생했습니다.\n{e}")

def main():
    root = tk.Tk()
    app = CaptureMergeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
