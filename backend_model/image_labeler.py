import os
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from PIL import Image, ImageTk

# Enable high-DPI awareness on Windows
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class LabelTool:
    def __init__(self, master):
        self.master = master
        self.master.title('YOLOv11 Labeling Tool')
        # Apply high-DPI scaling
        self.master.tk.call('tk', 'scaling', 2.0)
        # Set default window size
        self.master.geometry('2160x1440')
        self.master.configure(bg='#2b2b2b')

        # Initialize styles for buttons and labels
        self._init_styles()

        # Toolbar
        toolbar = tk.Frame(master, bg='#2d2d30')
        toolbar.pack(side='top', fill='x')
        for btn_text, cmd in [('📂 Open', self.open_folder), ('◀ Prev', self.prev_image),
                              ('Next ▶', self.next_image), ('💾 Save', self.export)]:
            btn = ttk.Button(toolbar, text=btn_text, command=cmd, style='Editor.TButton')
            btn.pack(side='left', padx=8, pady=8)
        self.lbl_info = ttk.Label(toolbar, text='No folder loaded', style='Editor.TLabel')
        self.lbl_info.pack(side='right', padx=12)

        # Main pane
        main_pane = ttk.Panedwindow(master, orient='horizontal')
        main_pane.pack(fill='both', expand=True)

        # Canvas frame
        canvas_frame = tk.Frame(main_pane, bg='#1e1e1e')
        main_pane.add(canvas_frame, weight=3)
        self.canvas = tk.Canvas(canvas_frame, bg='#1e1e1e', cursor='cross', highlightthickness=0)
        ybar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        xbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        ybar.pack(side='right', fill='y')
        xbar.pack(side='bottom', fill='x')
        self.canvas.pack(fill='both', expand=True)

        # Side panel for annotations list
        list_frame = tk.Frame(main_pane, bg='#252526', width=280)
        main_pane.add(list_frame, weight=1)
        header = ttk.Label(list_frame, text='Annotations', style='Editor.SideHeader.TLabel')
        header.pack(padx=12, pady=10)
        self.box_list = tk.Listbox(list_frame, bg='#252526', fg='white', bd=0, highlightthickness=0,
                                   font=('Consolas', 12), selectbackground='#264f78')
        self.box_list.pack(fill='both', expand=True, padx=12, pady=8)

        # Status bar
        self.status = ttk.Label(master, text='Ready', style='Editor.Status.TLabel', anchor='w')
        self.status.pack(side='bottom', fill='x')

        # Internal state
        self.image_dir = ''
        self.image_list = []
        self.cur = 0
        self.image = None
        self.tkimg = None
        self.boxes = {}
        self.start_x = self.start_y = None

        # Bind events
        self.canvas.bind('<ButtonPress-1>', self.on_button_press)
        self.canvas.bind('<B1-Motion>', self.on_move_press)
        self.canvas.bind('<ButtonRelease-1>', self.on_button_release)

    def _init_styles(self):
        style = ttk.Style(self.master)
        style.theme_use('clam')
        style.configure('Editor.TButton', background='#3e3e42', foreground='white',
                        font=('Consolas', 12), borderwidth=0, padding=6)
        style.map('Editor.TButton', background=[('active','#505050')])
        style.configure('Editor.TLabel', background='#2d2d30', foreground='white',
                        font=('Consolas', 12))
        style.configure('Editor.SideHeader.TLabel', background='#252526', foreground='white',
                        font=('Consolas', 13, 'bold'))
        style.configure('Editor.Status.TLabel', background='#007acc', foreground='white',
                        font=('Consolas', 11), padding=4)

    def open_folder(self):
        dirname = filedialog.askdirectory(title='Select Image Directory')
        if not dirname:
            return
        self.image_dir = dirname
        self.image_list = sorted([f for f in os.listdir(dirname)
                                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if not self.image_list:
            messagebox.showwarning('Warning', 'No images found!')
            return
        self.boxes = {i: [] for i in range(len(self.image_list))}
        self.cur = 0
        self.load_image()

    def load_image(self):
        img_path = os.path.join(self.image_dir, self.image_list[self.cur])
        self.image = Image.open(img_path)
        self.width, self.height = self.image.size
        self.tkimg = ImageTk.PhotoImage(self.image)
        self.canvas.delete('all')
        self.canvas.config(scrollregion=(0, 0, self.width, self.height))
        self.canvas.create_image(0, 0, anchor='nw', image=self.tkimg)
        for box in self.boxes.get(self.cur, []):
            self.draw_saved_box(box)
        self.master.title(f'YOLOv11 Labeling Tool - {self.image_list[self.cur]}')
        self.status.config(text=f'Image {self.cur+1}/{len(self.image_list)}')
        self.box_list.delete(0, 'end')
        for box in self.boxes.get(self.cur, []):
            self.box_list.insert('end',
                                 f"Class {box['class_id']}: ({box['xmin']:.1f},{box['ymin']:.1f})-({box['xmax']:.1f},{box['ymax']:.1f})")

    def prev_image(self):
        if self.cur > 0:
            self.cur -= 1
            self.load_image()

    def next_image(self):
        if self.cur < len(self.image_list) - 1:
            self.cur += 1
            self.load_image()

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='#c586c0', width=2)

    def on_move_press(self, event):
        curX = self.canvas.canvasx(event.x)
        curY = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        # Correctly sort coordinates for xmin,xmax and ymin,ymax
        xmin, xmax = sorted((self.start_x, end_x))
        ymin, ymax = sorted((self.start_y, end_y))
        class_id = simpledialog.askinteger('Input', 'Class ID:', parent=self.master)
        if class_id is None:
            self.canvas.delete(self.rect)
            return
        box = {'class_id': class_id, 'xmin': xmin, 'ymin': ymin,
               'xmax': xmax, 'ymax': ymax}
        self.boxes[self.cur].append(box)
        self.draw_saved_box(box)
        self.box_list.insert('end', f"Class {class_id}: ({xmin:.1f},{ymin:.1f})-({xmax:.1f},{ymax:.1f})")

    def draw_saved_box(self, box):
        xmin, ymin, xmax, ymax = (box['xmin'], box['ymin'], box['xmax'], box['ymax'])
        # draw rectangle
        self.canvas.create_rectangle(xmin, ymin, xmax, ymax,
                                     outline='#c586c0', width=2)
        # place label inside bottom-left corner (5px inset)
        label_x = xmin + 5
        label_y = ymax - 5
        self.canvas.create_text(label_x, label_y, text=str(box['class_id']),
                                anchor='sw', font=('Consolas', 12, 'bold'), fill='#c586c0')

    def export(self):
        outdir = filedialog.askdirectory(title='Select Export Folder')
        if not outdir:
            return
        img_out = os.path.join(outdir, 'images')
        lbl_out = os.path.join(outdir, 'labels')
        os.makedirs(img_out, exist_ok=True)
        os.makedirs(lbl_out, exist_ok=True)
        for idx, fname in enumerate(self.image_list):
            shutil.copy2(os.path.join(self.image_dir, fname), os.path.join(img_out, fname))
            with open(os.path.join(lbl_out, os.path.splitext(fname)[0]+'.txt'), 'w') as f:
                for box in self.boxes.get(idx, []):
                    x_center = (box['xmin'] + box['xmax']) / 2.0 / self.width
                    y_center = (box['ymin'] + box['ymax']) / 2.0 / self.height
                    w = (box['xmax'] - box['xmin']) / self.width
                    h = (box['ymax'] - box['ymin']) / self.height
                    f.write(f"{box['class_id']} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
        messagebox.showinfo('Export', f'Labeled data exported to {outdir}')

if __name__ == '__main__':
    root = tk.Tk()
    tool = LabelTool(root)
    root.mainloop()
