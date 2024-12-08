import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import fitz  
import google.generativeai as genai  
import os
import re
import time

genai.configure(api_key="AIzaSyAoapsmhtyLjkdEwfgEMNyivtEmSSdsVhA")  

class PDFMCQApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF MCQ App")
        self.pdf_doc = None
        self.current_page = 0
        self.mcq_data = None
        self.mcq_window = None  

        self.canvas = tk.Canvas(root, width=600, height=750)
        self.canvas.grid(row=0, column=0, rowspan=3)

        self.btn_frame = tk.Frame(root)
        self.btn_frame.grid(row=3, column=0, sticky="n")

        self.open_btn = tk.Button(self.btn_frame, text="Open PDF", command=self.open_pdf)
        self.open_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.prev_btn = tk.Button(self.btn_frame, text="Previous Page", command=self.previous_page, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.next_btn = tk.Button(self.btn_frame, text="Next Page", command=self.next_page, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.gen_btn = tk.Button(self.btn_frame, text="Generate MCQs", command=self.switch_to_mcqs, state=tk.DISABLED)
        self.gen_btn.pack(side=tk.LEFT, padx=10, pady=5)

    def switch_to_mcqs(self):

        self.canvas.destroy()
        self.btn_frame.destroy()

        self.questions_canvas = tk.Canvas(self.root, width=600, height=700, bd=0, highlightthickness=0)
        self.questions_canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.questions_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.questions_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.questions_canvas.yview)

        self.questions_frame = tk.Canvas(self.questions_canvas, width=580, height=680)
        self.questions_canvas.create_window((10, 10), window=self.questions_frame, anchor="nw")

        question_label = tk.Label(
            self.questions_frame, text="", justify="left", font=("Arial", 12)
        )
        question_label.pack(pady=10)

        self.var = tk.StringVar(value="")
        self.options_frame = tk.Frame(self.questions_frame)
        self.options_frame.pack()

        self.submit_btn = tk.Button(self.questions_frame, text="Submit Answer", command=self.submit_answer, state=tk.DISABLED)
        self.submit_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.back_btn = tk.Button(self.questions_frame, text="Return to PDF", command=self.switch_to_pdf, state=tk.NORMAL)
        self.back_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.generate_mcq()

        self.questions_canvas.focus_set()

        self.questions_canvas.bind_all("<Up>", self.scroll_up)
        self.questions_canvas.bind_all("<Down>", self.scroll_down)
        self.questions_canvas.bind_all("<MouseWheel>", self.scroll_with_mouse)

        self.questions_frame.update_idletasks()
        self.questions_canvas.update_idletasks()
        self.questions_canvas.bind_all("<Configure>", self.update_scrollregion)

    def update_scrollregion(self, event=None):

            self.questions_canvas.configure(scrollregion=self.questions_canvas.bbox("all"))

    def scroll_with_mouse(self, event):
        if event.delta > 0:
            self.questions_canvas.yview_scroll(-1, "units")
        else:
            self.questions_canvas.yview_scroll(1, "units")

    def scroll_up(self, event):

        self.questions_canvas.yview_scroll(-1, "units")

    def scroll_down(self, event):

        self.questions_canvas.yview_scroll(1, "units")

    def start_func(self):
        global start_num
        start_num = self.current_page

    def end_func(self):
        global end_num
        end_num = self.current_page

    def switch_to_pdf(self):

        if hasattr(self, 'questions_canvas') and self.questions_canvas:
            self.questions_canvas.destroy()
        if hasattr(self, 'scrollbar') and self.scrollbar:
            self.scrollbar.destroy()

        self.__init__(root)

        self.canvas.update_idletasks()

        self.re_open_pdf(file_path, end_num)

        self.canvas.update_idletasks()

    def open_pdf(self):

        global file_path
        filepath = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        file_path = filepath
        print(filepath, file_path)
        if not filepath:
            return

        try:

            self.pdf_doc = fitz.open(file_path)
            self.current_page = 0
            self.display_page(self.current_page)

            self.prev_btn.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            self.gen_btn.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")

    def re_open_pdf(self, path, page_num):

        try:

            self.pdf_doc = fitz.open(file_path)
            self.current_page=page_num
            print(page_num)
            self.display_page(self.current_page)

            self.prev_btn.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            self.gen_btn.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to re-open PDF: {e}")

    def display_page(self, page_num):
        if self.pdf_doc is None:
            return

        global page
        print(page_num)
        page = self.pdf_doc[page_num]
        pix = page.get_pixmap()
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

    def generate_mcq(self):
        try:

            self.start_func()
            self.end_func()
            temp_file_path = "temp_page.pdf"
            doc = fitz.open()  

            for i in range(start_num, end_num+1):
                            page_text=self.pdf_doc[i].get_text()
                            mpage = doc.new_page()  
                            mpage.insert_text((72, 72), page_text)  

            doc.save(temp_file_path)  
            doc.close()

            def upload_to_gemini(path, mime_type="application/pdf"):
                file = genai.upload_file(path, mime_type=mime_type)
                return file

            def wait_for_files_active(files):
                for name in (file.name for file in files):
                    file = genai.get_file(name)
                    while file.state.name == "PROCESSING":
                        time.sleep(2)
                        file = genai.get_file(name)
                    if file.state.name != "ACTIVE":
                        raise Exception(f"File {file.name} failed to process")

            uploaded_file = upload_to_gemini(temp_file_path)
            wait_for_files_active([uploaded_file])

            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash", generation_config=generation_config
            )

            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [
                            uploaded_file,
                            "Generate 10 multiple-choice questions from the PDF page. Format the answers accoding to this regex format: question_pattern => ^\\*\\*(\\d+)\\.\\s+(.*)\\*\\*$, option_pattern => ^\\((a|b|c|d)\\)\\s+(.*)$, answer_pattern => ^\\*\\*Answer:\\s+\\((a|b|c|d)\\)\\s+(.*)\\*\\*$. Do not add any extra text or formatting.",
                        ],
                    }
                ]
            )

            response = chat_session.send_message("Proceed with question generation")
            mcq_text = response.text
            print("Gemini API Response:", response.text)

            self.mcq_data = self.parse_mcq(mcq_text)
            self.display_mcq()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate MCQs: {e}")
            self.mcq_data = None
            self.question_label.config(text="Failed to load MCQs. Please try again.")

        finally:

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def parse_mcq(self, mcq_text):
        try:

            lines = mcq_text.strip().split("\n")

            questions = []
            options = {}
            correct_answers = {}

            question_pattern = re.compile(r"^\*\*(\d+)\.\s+(.*)\*\*$")
            option_pattern = re.compile(r"^\((a|b|c|d)\)\s+(.*)$")
            answer_pattern = re.compile(r"^\*\*Answer:\s+\((a|b|c|d)\)\s+(.*)\*\*$")

            current_question = None
            for line in lines:

                question_match = question_pattern.match(line)
                if question_match:
                    current_question = question_match.group(2).strip()
                    questions.append(current_question)
                    options[current_question] = []
                    continue

                option_match = option_pattern.match(line)
                if option_match and current_question:
                    options[current_question].append(f"({option_match.group(1)}) {option_match.group(2).strip()}")
                    continue

                answer_match = answer_pattern.match(line)
                if answer_match and current_question:
                    correct_answers[current_question] = f"({answer_match.group(1)}) {answer_match.group(2).strip()}"
                    continue

            if not questions or not correct_answers:
                raise ValueError("Incomplete or improperly formatted MCQ data.")

            return {
                "questions": questions,
                "options": options,
                "correct_answers": correct_answers
            }
        except Exception as e:
            print("Error parsing MCQ:", e)  
            return {"questions": [], "options": {}, "correct_answers": {}}

    def display_mcq(self):
        if not self.mcq_data or "questions" not in self.mcq_data or "options" not in self.mcq_data:
            self.question_label.config(text="No MCQs available for this page.")
            self.submit_btn.config(state=tk.DISABLED)
            return

        self.answer_vars = []
        j=1
        for question in self.mcq_data["questions"]:
            question_text = f"{j}. {question}"
            tk.Label(self.options_frame, text=question_text, wraplength=550, justify="left", anchor="w", font=("Arial", 12)).pack(pady=5, fill="x", anchor="w")
            j+=1
            var=tk.StringVar(value="NONE")
            self.answer_vars.append(var)
            for option in self.mcq_data["options"][question]:
                tk.Radiobutton(
                    self.options_frame, text=option, variable=var, value=option, indicatoron=True
                ).pack(anchor=tk.W)
                print(option)

        self.submit_btn.config(state=tk.NORMAL)

    def submit_answer(self):
        all_correct = True
        for i, question in enumerate(self.mcq_data["questions"]):
            selected_answer = self.answer_vars[i].get()
            if not selected_answer:
                messagebox.showwarning("Warning", f"Please select an answer for question {i + 1}.")
                return

            if selected_answer != self.mcq_data["correct_answers"][question]:
                all_correct = False

        if all_correct:
            messagebox.showinfo("Correct!", "You answered all questions correctly! Proceeding back to the main window.")
            self.switch_to_pdf()
        else:
            messagebox.showerror("Incorrect!", "One or more answers are incorrect. Try again.")
            self.submit_btn.config(state=tk.NORMAL)

    def next_page(self):
        if self.pdf_doc is None or self.current_page >= len(self.pdf_doc) - 1:
            messagebox.showinfo("End of PDF", "You have reached the end of the PDF.")
            return
        self.current_page += 1
        self.display_page(self.current_page)

    def previous_page(self):
        if self.current_page==0:
            messagebox.showinfo("Beginning of the PDF", "There is no previous page to go back to.")
            return
        self.current_page -= 1
        self.display_page(self.current_page)

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFMCQApp(root)
    root.mainloop()