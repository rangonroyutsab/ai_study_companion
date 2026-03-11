import tkinter as tk
from app.pdf_viewer import PDFViewer

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFViewer(root)
    root.mainloop()