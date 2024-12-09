import tkinter as tk
from tkinter import messagebox
import fitz
import google.generativeai as genai
import os
import re
import time

genai.configure(api_key="AIzaSyAoapsmhtyLjkdEwfgEMNyivtEmSSdsVhA")

class MCQGenerator:
    def __init__(self, root, pdf_doc, current_page):
        self.root = root
        self.pdf_doc = pdf_doc
        self.current_page = current_page
        self.mcq_data = None
        self.setup_ui()
        self.generate_mcq()

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        self.mcq_wrapper_frame = tk.Frame(self.root)
        self.mcq_wrapper_frame.grid(row=1, column=1)

        self.questions_canvas = tk.Canvas(self.mcq_wrapper_frame, width=600, height=750, bd=0, highlightthickness=0)
        self.questions_canvas.grid(row=0, column=0, pady=5)

        self.scrollbar = tk.Scrollbar(self.mcq_wrapper_frame, orient="vertical", command=self.questions_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.ques_btn_frame = tk.Frame(self.mcq_wrapper_frame)
        self.ques_btn_frame.grid(row=1, column=0, sticky="n")

        self.questions_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.questions_canvas.yview)

        self.questions_frame = tk.Canvas(self.questions_canvas, width=580, height=730)
        self.questions_canvas.create_window((10, 0), window=self.questions_frame, anchor="nw")

        self.question_label = tk.Label(self.questions_frame, text="", justify="left", font=("Arial", 12))
        self.question_label.pack(pady=10)

        self.var = tk.StringVar(value="")
        self.options_frame = tk.Frame(self.questions_frame)
        self.options_frame.pack()

        self.submit_btn = tk.Button(self.ques_btn_frame, text="Submit Answer", command=self.submit_answer, state=tk.DISABLED)
        self.submit_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.back_btn = tk.Button(self.ques_btn_frame, text="Return to PDF", command=self.switch_to_pdf, state=tk.NORMAL)
        self.back_btn.pack(side=tk.LEFT, padx=10, pady=5)

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

    def switch_to_pdf(self):
        self.mcq_wrapper_frame.destroy()
        PDFViewer(self.root)

    def generate_mcq(self):
        try:
            temp_file_path = "temp_page.pdf"
            doc = fitz.open()

            page_text = self.pdf_doc[self.current_page].get_text()
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
                            "Generate 10 multiple-choice questions from the PDF page. Format the answers according to this regex format: question_pattern => ^\\*\\*(\\d+)\\.\\s+(.*)\\*\\*$, option_pattern => ^\\((a|b|c|d)\\)\\s+(.*)$, answer_pattern => ^\\*\\*Answer:\\s+\\((a|b|c|d)\\)\\s+(.*)\\*\\*$. Do not add any extra text or formatting.",
                        ],
                    }
                ]
            )

            response = chat_session.send_message("Proceed with question generation")
            mcq_text = response.text

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
        for i, question in enumerate(self.mcq_data["questions"]):
            question_text = f"{i + 1}. {question}"
            tk.Label(self.options_frame, text=question_text, wraplength=550, justify="left", anchor="w", font=("Arial", 16)).pack(pady=(10, 5), fill="x", anchor="w")
            var = tk.StringVar(value="NONE")
            self.answer_vars.append(var)
            for option in self.mcq_data["options"][question]:
                tk.Radiobutton(
                    self.options_frame, text=option, variable=var, value=option, indicatoron=True
                ).pack(anchor=tk.W)

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