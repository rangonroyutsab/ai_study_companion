"""
Test suite for AI Study Companion.

Heavy dependencies (tkinter, fitz, PIL) are patched into sys.modules at module
level — before any app module is imported — so no GUI windows open and no real
API calls are made during testing.
"""

import sys
import os
import importlib
from unittest.mock import MagicMock, patch

import pytest

# ── Patch GUI / C-extension modules before importing any app code ─────────────
_mock_tk = MagicMock()
_mock_tk.DISABLED = "disabled"
_mock_tk.NORMAL = "normal"
_mock_tk.LEFT = "left"
_mock_tk.W = "w"
_mock_tk.CENTER = "center"
sys.modules["tkinter"] = _mock_tk
sys.modules["tkinter.messagebox"] = _mock_tk.messagebox
sys.modules["tkinter.filedialog"] = _mock_tk.filedialog

_mock_pil = MagicMock()
sys.modules["PIL"] = _mock_pil
sys.modules["PIL.Image"] = _mock_pil.Image
sys.modules["PIL.ImageTk"] = _mock_pil.ImageTk

sys.modules["fitz"] = MagicMock()

# ── App imports (after patching) ──────────────────────────────────────────────
import app.utils as utils_module
from app.pdf_viewer import PDFViewer
from app.mcq_generator import MCQGenerator

# ── Shared test fixtures ──────────────────────────────────────────────────────

WELL_FORMED_MCQ = (
    "**1. What is the capital of France?**\n"
    "(a) London\n"
    "(b) Berlin\n"
    "(c) Paris\n"
    "(d) Madrid\n"
    "**Answer: (c) Paris**\n"
    "\n"
    "**2. What is 2 + 2?**\n"
    "(a) 3\n"
    "(b) 4\n"
    "(c) 5\n"
    "(d) 6\n"
    "**Answer: (b) 4**\n"
)

_MCQ_DATA_SINGLE = {
    "questions": ["What is the capital of France?"],
    "options": {
        "What is the capital of France?": [
            "(a) London",
            "(b) Berlin",
            "(c) Paris",
            "(d) Madrid",
        ]
    },
    "correct_answers": {"What is the capital of France?": "(c) Paris"},
}


def _make_pdf_viewer():
    """PDFViewer backed by a MagicMock root — no real Tk window."""
    return PDFViewer(MagicMock())


def _make_mcq_generator(mcq_data=None):
    """
    MCQGenerator with setup_ui and generate_mcq stubbed out so the constructor
    completes without touching tkinter or the Gemini API.  Widget attributes
    that setup_ui would normally create are replaced with fresh MagicMocks.
    """
    with patch.object(MCQGenerator, "setup_ui"), \
         patch.object(MCQGenerator, "generate_mcq"):
        gen = MCQGenerator(MagicMock(), MagicMock(), 0)
    gen.question_label = MagicMock()
    gen.submit_btn = MagicMock()
    gen.options_frame = MagicMock()
    gen.mcq_wrapper_frame = MagicMock()
    gen.mcq_data = mcq_data
    return gen


# ═════════════════════════════════════════════════════════════════════════════
# PDFViewer tests
# ═════════════════════════════════════════════════════════════════════════════

class TestPDFViewerOpenPDF:
    def test_open_pdf_success(self):
        viewer = _make_pdf_viewer()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=5)

        with patch("app.pdf_viewer.filedialog.askopenfilename", return_value="/path/to/test.pdf"), \
             patch("app.pdf_viewer.fitz.open", return_value=mock_doc), \
             patch.object(viewer, "display_page"):
            viewer.open_pdf()

        assert viewer.pdf_doc is mock_doc
        assert viewer.current_page == 0
        assert viewer.total_pages == 5

    def test_open_pdf_cancelled_does_nothing(self):
        viewer = _make_pdf_viewer()
        with patch("app.pdf_viewer.filedialog.askopenfilename", return_value=""):
            viewer.open_pdf()
        assert viewer.pdf_doc is None


class TestPDFViewerNavigation:
    def _viewer_with_doc(self, num_pages=3, current_page=0):
        viewer = _make_pdf_viewer()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=num_pages)
        viewer.pdf_doc = mock_doc
        viewer.current_page = current_page
        viewer.total_pages = num_pages
        return viewer

    def test_next_page_increments_current_page(self):
        viewer = self._viewer_with_doc(num_pages=3, current_page=0)
        with patch.object(viewer, "display_page") as mock_display:
            viewer.next_page()
        assert viewer.current_page == 1
        mock_display.assert_called_once_with(1)

    def test_next_page_at_last_page_shows_info_and_does_not_increment(self):
        viewer = self._viewer_with_doc(num_pages=3, current_page=2)
        with patch("app.pdf_viewer.messagebox.showinfo") as mock_info:
            viewer.next_page()
        mock_info.assert_called_once()
        assert viewer.current_page == 2

    def test_previous_page_at_zero_shows_info_and_does_not_decrement(self):
        viewer = self._viewer_with_doc(current_page=0)
        with patch("app.pdf_viewer.messagebox.showinfo") as mock_info:
            viewer.previous_page()
        mock_info.assert_called_once()
        assert viewer.current_page == 0

    def test_previous_page_decrements_current_page(self):
        viewer = self._viewer_with_doc(current_page=2)
        with patch.object(viewer, "display_page") as mock_display:
            viewer.previous_page()
        assert viewer.current_page == 1
        mock_display.assert_called_once_with(1)


class TestPDFViewerJumpToPage:
    def _viewer_with_doc(self, total_pages=5):
        viewer = _make_pdf_viewer()
        viewer.pdf_doc = MagicMock()
        viewer.total_pages = total_pages
        viewer.page_entry = MagicMock()
        return viewer

    def test_jump_to_valid_page(self):
        viewer = self._viewer_with_doc()
        viewer.page_entry.get.return_value = "3/5"
        with patch.object(viewer, "display_page") as mock_display:
            viewer.jump_to_page()
        assert viewer.current_page == 2  # 3 - 1
        mock_display.assert_called_once_with(2)

    def test_jump_to_out_of_range_page_shows_error(self):
        viewer = self._viewer_with_doc()
        viewer.page_entry.get.return_value = "10/5"
        with patch("app.pdf_viewer.tk") as mock_tk_module:
            viewer.jump_to_page()
        mock_tk_module.messagebox.showerror.assert_called_once()

    def test_jump_to_non_numeric_page_shows_error(self):
        viewer = self._viewer_with_doc()
        viewer.page_entry.get.return_value = "abc"
        with patch("app.pdf_viewer.tk") as mock_tk_module:
            viewer.jump_to_page()
        mock_tk_module.messagebox.showerror.assert_called_once()


class TestPDFViewerSwitchToMCQs:
    def test_switch_to_mcqs_destroys_widgets_and_creates_mcq_generator(self):
        viewer = _make_pdf_viewer()
        mock_doc = MagicMock()
        viewer.pdf_doc = mock_doc
        viewer.current_page = 1

        with patch("app.pdf_viewer.MCQGenerator") as mock_mcq_cls:
            viewer.switch_to_mcqs()

        viewer.canvas.destroy.assert_called_once()
        viewer.btn_frame.destroy.assert_called_once()
        mock_mcq_cls.assert_called_once_with(viewer.root, mock_doc, 1)


# ═════════════════════════════════════════════════════════════════════════════
# MCQGenerator tests
# ═════════════════════════════════════════════════════════════════════════════

class TestParseMCQ:
    def test_parse_mcq_well_formed_returns_correct_structure(self):
        gen = _make_mcq_generator()
        result = gen.parse_mcq(WELL_FORMED_MCQ)

        assert result["questions"] == [
            "What is the capital of France?",
            "What is 2 + 2?",
        ]
        assert result["correct_answers"]["What is the capital of France?"] == "(c) Paris"
        assert result["correct_answers"]["What is 2 + 2?"] == "(b) 4"
        assert "(a) London" in result["options"]["What is the capital of France?"]
        assert "(c) Paris" in result["options"]["What is the capital of France?"]

    def test_parse_mcq_malformed_text_returns_empty_structure(self):
        gen = _make_mcq_generator()
        result = gen.parse_mcq("This is not valid MCQ text at all.")
        assert result == {"questions": [], "options": {}, "correct_answers": {}}

    def test_parse_mcq_empty_string_returns_empty_structure(self):
        gen = _make_mcq_generator()
        result = gen.parse_mcq("")
        assert result == {"questions": [], "options": {}, "correct_answers": {}}


class TestDisplayMCQ:
    def test_display_mcq_with_none_data_disables_submit_button(self):
        gen = _make_mcq_generator(mcq_data=None)
        gen.display_mcq()
        gen.submit_btn.config.assert_called_with(state="disabled")

    def test_display_mcq_with_missing_keys_disables_submit_button(self):
        gen = _make_mcq_generator(mcq_data={})
        gen.display_mcq()
        gen.submit_btn.config.assert_called_with(state="disabled")


class TestSubmitAnswer:
    def test_submit_all_correct_shows_success_and_switches_to_pdf(self):
        gen = _make_mcq_generator(mcq_data=_MCQ_DATA_SINGLE)
        correct_var = MagicMock()
        correct_var.get.return_value = "(c) Paris"
        gen.answer_vars = [correct_var]

        with patch.object(gen, "switch_to_pdf") as mock_switch, \
             patch("app.mcq_generator.messagebox.showinfo"):
            gen.submit_answer()

        mock_switch.assert_called_once()

    def test_submit_wrong_answer_shows_error_and_keeps_submit_enabled(self):
        gen = _make_mcq_generator(mcq_data=_MCQ_DATA_SINGLE)
        wrong_var = MagicMock()
        wrong_var.get.return_value = "(a) London"
        gen.answer_vars = [wrong_var]

        with patch("app.mcq_generator.messagebox.showerror") as mock_err:
            gen.submit_answer()

        mock_err.assert_called_once()
        gen.submit_btn.config.assert_called_with(state="normal")


# ═════════════════════════════════════════════════════════════════════════════
# utils tests
# ═════════════════════════════════════════════════════════════════════════════

class TestUtils:
    def test_client_is_initialized_on_import(self):
        assert utils_module.client is not None

    def test_load_dotenv_is_called_on_import(self):
        mock_dotenv = MagicMock()
        with patch.dict(sys.modules, {"dotenv": mock_dotenv}):
            importlib.reload(utils_module)
        mock_dotenv.load_dotenv.assert_called_once()
        importlib.reload(utils_module)  # restore real state

    def test_client_receives_api_key_from_environment(self):
        from google import genai as real_genai
        with patch.object(real_genai, "Client") as mock_client_cls, \
             patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-abc"}):
            importlib.reload(utils_module)
        mock_client_cls.assert_called_once_with(api_key="test-key-abc")
        importlib.reload(utils_module)  # restore real state

    def test_wait_for_files_active_succeeds_when_file_already_active(self):
        input_file = MagicMock()
        input_file.name = "files/test-123"
        active_file = MagicMock()
        active_file.state.name = "ACTIVE"
        active_file.name = "files/test-123"

        with patch("app.utils.client") as mock_client, \
             patch("app.utils.time.sleep"):
            mock_client.files.get.return_value = active_file
            utils_module.wait_for_files_active([input_file])  # must not raise

        mock_client.files.get.assert_called_once_with(name="files/test-123")

    def test_wait_for_files_active_polls_until_active(self):
        input_file = MagicMock()
        input_file.name = "files/test-456"

        processing = MagicMock()
        processing.state.name = "PROCESSING"
        processing.name = "files/test-456"

        active = MagicMock()
        active.state.name = "ACTIVE"
        active.name = "files/test-456"

        with patch("app.utils.client") as mock_client, \
             patch("app.utils.time.sleep") as mock_sleep:
            mock_client.files.get.side_effect = [processing, active]
            utils_module.wait_for_files_active([input_file])

        assert mock_client.files.get.call_count == 2
        assert mock_sleep.call_count == 1

    def test_wait_for_files_active_raises_when_file_failed(self):
        input_file = MagicMock()
        input_file.name = "files/test-789"

        failed_file = MagicMock()
        failed_file.state.name = "FAILED"
        failed_file.name = "files/test-789"

        with patch("app.utils.client") as mock_client, \
             patch("app.utils.time.sleep"):
            mock_client.files.get.return_value = failed_file
            with pytest.raises(Exception, match="failed to process"):
                utils_module.wait_for_files_active([input_file])
