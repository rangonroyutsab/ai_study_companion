import tkinter as tk
from pdf_viewer import PDFViewer
from mcq_generator import MCQGenerator

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFViewer(root)
    root.mainloop()