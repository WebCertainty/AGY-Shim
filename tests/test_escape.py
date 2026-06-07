import unittest
import sys
import os

# Set up paths to import from src/agy_shim
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from agy_shim.main import escape_plain_text_backslashes, get_stable_raw_text

class TestEscapeBackslashes(unittest.TestCase):
    def test_basic_path_escaping(self):
        # dot
        self.assertEqual(
            escape_plain_text_backslashes("D:\\CODE-REPO\\.git\\index.lock"),
            "D:\\CODE-REPO\\\\.git\\index.lock"
        )
        # underscore
        self.assertEqual(
            escape_plain_text_backslashes("C:\\Users\\eflyers\\__init__.py"),
            "C:\\Users\\eflyers\\\\\\_\\_init\\_\\_.py"
        )
        # dash
        self.assertEqual(
            escape_plain_text_backslashes("C:\\temp\\-debug.log"),
            "C:\\temp\\\\-debug.log"
        )

    def test_letters_not_escaped(self):
        self.assertEqual(
            escape_plain_text_backslashes("scripts\\run-daily-briefing.ps1"),
            "scripts\\run-daily-briefing.ps1"
        )
        self.assertEqual(
            escape_plain_text_backslashes("Tools\\clairvoyance-daily-briefing\\AGENTS.md"),
            "Tools\\clairvoyance-daily-briefing\\AGENTS.md"
        )
        self.assertEqual(
            escape_plain_text_backslashes(".git\\index.lock"),
            ".git\\index.lock"
        )

    def test_inside_code_block(self):
        self.assertEqual(
            escape_plain_text_backslashes("```\nD:\\CODE-REPO\\.git\\index.lock\n```"),
            "```\nD:\\CODE-REPO\\.git\\index.lock\n```"
        )
        self.assertEqual(
            escape_plain_text_backslashes("~~~\nD:\\CODE-REPO\\.git\\index.lock\n~~~"),
            "~~~\nD:\\CODE-REPO\\.git\\index.lock\n~~~"
        )

    def test_inside_inline_code(self):
        self.assertEqual(
            escape_plain_text_backslashes("`D:\\CODE-REPO\\.git\\index.lock`"),
            "`D:\\CODE-REPO\\.git\\index.lock`"
        )

    def test_unclosed_blocks_are_treated_as_code(self):
        # unclosed inline code
        self.assertEqual(
            escape_plain_text_backslashes("`D:\\CODE-REPO\\.git\\index.lock"),
            "`D:\\CODE-REPO\\.git\\index.lock"
        )
        # unclosed fenced code block
        self.assertEqual(
            escape_plain_text_backslashes("```\nD:\\CODE-REPO\\.git\\index.lock"),
            "```\nD:\\CODE-REPO\\.git\\index.lock"
        )

    def test_mixed_text(self):
        inp = "Check this path: D:\\CODE-REPO\\.git\\index.lock and also `code \\. block` then other path D:\\CODE-REPO\\.git\\index.lock"
        expected = "Check this path: D:\\CODE-REPO\\\\.git\\index.lock and also `code \\. block` then other path D:\\CODE-REPO\\\\.git\\index.lock"
        self.assertEqual(escape_plain_text_backslashes(inp), expected)

    def test_escaped_backtick_no_inline_state(self):
        # Escaped backticks/tildes should not trigger inline-code escaping-bypass state
        inp = "Some escaped backtick: \\` then path D:\\CODE-REPO\\.git\\index.lock"
        expected = "Some escaped backtick: \\\\` then path D:\\CODE-REPO\\\\.git\\index.lock"
        self.assertEqual(escape_plain_text_backslashes(inp), expected)

    def test_stable_raw_text(self):
        # Trailing backslash is unstable
        self.assertEqual(get_stable_raw_text("D:\\"), ("D:", "\\"))
        # Trailing odd underscore is unstable
        self.assertEqual(get_stable_raw_text("some_"), ("some", "_"))
        self.assertEqual(get_stable_raw_text("some__"), ("some__", ""))
        self.assertEqual(get_stable_raw_text("some___"), ("some__", "_"))
        # Trailing odd/short backtick is unstable
        self.assertEqual(get_stable_raw_text("code`"), ("code", "`"))
        self.assertEqual(get_stable_raw_text("code``"), ("code", "``"))
        self.assertEqual(get_stable_raw_text("code```"), ("code```", ""))
        # Trailing odd/short tilde is unstable
        self.assertEqual(get_stable_raw_text("code~"), ("code", "~"))
        self.assertEqual(get_stable_raw_text("code~~"), ("code", "~~"))
        self.assertEqual(get_stable_raw_text("code~~~"), ("code~~~", ""))

if __name__ == "__main__":
    unittest.main()
