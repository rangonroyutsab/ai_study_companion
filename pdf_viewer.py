import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import fitz
from mcq_generator import MCQGenerator

class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF MCQ App")
        self.pdf_doc = None
        self.current_page = 0
        self.current_page_var = tk.StringVar()
        self.total_pages = 0

        self.setup_ui()

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        self.wrapper_frame = tk.Frame(self.root)
        self.wrapper_frame.grid(row=1, column=1)
        self.wrapper_frame.grid_rowconfigure(0, weight=1)
        self.wrapper_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.wrapper_frame, width=600, height=750)
        self.canvas.grid(row=0, column=0, pady=5)

        self.btn_frame = tk.Frame(self.wrapper_frame)
        self.btn_frame.grid(row=1, column=0)
        self.btn_frame.columnconfigure(0, weight=1)

        self.open_btn = tk.Button(self.btn_frame, text="Open PDF", command=self.open_pdf)
        self.open_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.prev_btn = tk.Button(self.btn_frame, text="Previous Page", command=self.previous_page, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.page_entry = tk.Entry(self.btn_frame, textvariable=self.current_page_var, width=10, justify="center")
        self.page_entry.pack(side=tk.LEFT, padx=10, pady=5)
        self.page_entry.bind("<Return>", self.jump_to_page)

        self.next_btn = tk.Button(self.btn_frame, text="Next Page", command=self.next_page, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.gen_btn = tk.Button(self.btn_frame, text="Generate MCQs", command=self.switch_to_mcqs, state=tk.DISABLED)
        self.gen_btn.pack(side=tk.LEFT, padx=10, pady=5)

    def open_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not filepath:
            return

        try:
            self.pdf_doc = fitz.open(filepath)
            self.current_page = 0
            self.total_pages = len(self.pdf_doc)
            self.update_page_display()
            self.display_page(self.current_page)

            self.prev_btn.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            self.gen_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def display_page(self, page_num):
        if self.pdf_doc is None:
            return

        page = self.pdf_doc[page_num]
        matrix = fitz.Matrix(3, 3)
        pix = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        img_width, img_height = img.size
        width_scale = canvas_width / img_width
        height_scale = canvas_height / img_height

        new_width = int(img_width * width_scale)
        new_height = int(img_height * height_scale)

        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        self.img_tk = ImageTk.PhotoImage(img_resized)
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=self.img_tk)

    def next_page(self):
        if self.pdf_doc is None or self.current_page >= len(self.pdf_doc) - 1:
            messagebox.showinfo("End of PDF", "You have reached the end of the PDF.")
            return
        self.current_page += 1
        self.display_page(self.current_page)
        self.update_page_display()

    def previous_page(self):
        if self.current_page == 0:
            messagebox.showinfo("Beginning of the PDF", "There is no previous page to go back to.")
            return
        self.current_page -= 1
        self.display_page(self.current_page)
        self.update_page_display()

    def update_page_display(self):
        if self.pdf_doc is not None:
            self.current_page_var.set(f"{self.current_page + 1}/{self.total_pages}")
        else:
            self.current_page_var.set("0/0")

    def jump_to_page(self, event=None):
        if self.pdf_doc is None:
            return
        try:
            page_num = int(self.page_entry.get().split('/')[0]) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.display_page(self.current_page)
                self.update_page_display()
            else:
                tk.messagebox.showerror("Error", "Invalid page number.")
        except ValueError:
            tk.messagebox.showerror("Error", "Please enter a valid page number.")

    def switch_to_mcqs(self):
        self.canvas.destroy()
        self.btn_frame.destroy()
        MCQGenerator(self.root, self.pdf_doc, self.current_page)