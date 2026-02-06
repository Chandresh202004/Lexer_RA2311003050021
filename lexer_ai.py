import sys
import google.generativeai as genai

# ============================================================
#  CONFIGURATION - PASTE YOUR GEMINI API KEY HERE
# ============================================================
API_KEY = "AIzaSyADkflOgv5KDiUwlFfpOZAvHtIgRGc_ysU"

# ============================================================
#  TOKEN TYPES & TOKEN CLASS
# ============================================================
KEYWORDS = [
    "auto","break","case","char","const","continue","default","do",
    "double","else","enum","extern","float","for","goto","if",
    "int","long","register","return","short","signed","sizeof","static",
    "struct","switch","typedef","union","unsigned","void","volatile","while",
    "print","input","def","class","import","from","as","try","except",
    "finally","raise","with","yield","lambda","pass","True","False","None",
    "and","or","not","in","is","elif"
]

class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

# ============================================================
#  LEXER CLASS
# ============================================================
class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.errors = []

    def current_char(self):
        return self.source[self.pos] if self.pos < len(self.source) else None

    def peek_char(self):
        return self.source[self.pos + 1] if self.pos + 1 < len(self.source) else None

    def advance(self):
        if self.current_char() == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()

    def add_token(self, t, v, l, c):
        self.tokens.append(Token(t, v, l, c))

    def add_error(self, msg, line, col):
        self.errors.append(f"[Ln {line}, Col {col}] {msg}")

    # ---------- NUMBER ----------
    def lex_number(self):
        sl, sc = self.line, self.column
        num_str = ""
        is_float = False
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if is_float:
                    self.add_error(f"Invalid number: multiple decimal points", self.line, self.column)
                    break
                is_float = True
            num_str += self.current_char()
            self.advance()
        self.add_token("FLOAT" if is_float else "INTEGER", num_str, sl, sc)

    # ---------- IDENTIFIER / KEYWORD ----------
    def lex_identifier(self):
        sl, sc = self.line, self.column
        word = ""
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            word += self.current_char()
            self.advance()
        self.add_token("KEYWORD" if word in KEYWORDS else "IDENTIFIER", word, sl, sc)

    # ---------- STRING ----------
    def lex_string(self, q):
        sl, sc = self.line, self.column
        s = q
        self.advance()
        while self.current_char() and self.current_char() != q:
            if self.current_char() == '\\':
                s += self.current_char()
                self.advance()
            if self.current_char():
                s += self.current_char()
                self.advance()
        if self.current_char() == q:
            s += self.current_char()
            self.advance()
        else:
            self.add_error(f"Unterminated string starting with {q}", sl, sc)
        self.add_token("STRING", s, sl, sc)

    # ---------- SINGLE-LINE COMMENT ----------
    def lex_comment(self):
        sl, sc = self.line, self.column
        c = ""
        while self.current_char() and self.current_char() != '\n':
            c += self.current_char()
            self.advance()
        self.add_token("COMMENT", c, sl, sc)

    # ---------- MULTI-LINE COMMENT ----------
    def lex_multi_comment(self):
        sl, sc = self.line, self.column
        c = "/*"
        self.advance()
        self.advance()
        while self.current_char():
            if self.current_char() == '*' and self.peek_char() == '/':
                c += "*/"
                self.advance()
                self.advance()
                break
            c += self.current_char()
            self.advance()
        else:
            self.add_error("Unterminated multi-line comment", sl, sc)
        self.add_token("COMMENT", c, sl, sc)

    # ---------- PREPROCESSOR ----------
    def lex_preprocessor(self):
        sl, sc = self.line, self.column
        d = ""
        while self.current_char() and self.current_char() != '\n':
            d += self.current_char()
            self.advance()
        self.add_token("PREPROCESSOR", d, sl, sc)

    # ==================== MAIN TOKENIZE ====================
    def tokenize(self):
        multi_ops = [
            "==","!=","<=",">=","&&","||","++","--",
            "+=","-=","*=","/=","<<",">>","->","**","//"
        ]
        single_ops = set("+-*/%=<>!&|^~?:@")
        delims = set("(){}[];,.")

        while self.pos < len(self.source):
            self.skip_whitespace()
            ch = self.current_char()
            if ch is None:
                break
            if ch == '\n':
                self.advance()
                continue
            if ch == '#':
                self.lex_preprocessor()
                continue
            if ch == '/' and self.peek_char() == '/':
                self.lex_comment()
                continue
            if ch == '/' and self.peek_char() == '*':
                self.lex_multi_comment()
                continue
            if ch.isdigit():
                self.lex_number()
                continue
            if ch.isalpha() or ch == '_':
                self.lex_identifier()
                continue
            if ch in ('"', "'"):
                self.lex_string(ch)
                continue
            if self.peek_char() and ch + self.peek_char() in multi_ops:
                self.add_token("OPERATOR", ch + self.peek_char(), self.line, self.column)
                self.advance()
                self.advance()
                continue
            if ch in single_ops:
                self.add_token("OPERATOR", ch, self.line, self.column)
                self.advance()
                continue
            if ch in delims:
                self.add_token("DELIMITER", ch, self.line, self.column)
                self.advance()
                continue
            self.add_error(f"Unknown character: '{ch}'", self.line, self.column)
            self.add_token("UNKNOWN", ch, self.line, self.column)
            self.advance()

        return self.tokens


# ============================================================
#  AI SUGGESTION ENGINE (Google Gemini)
# ============================================================
class AIAssistant:
    def __init__(self, api_key):
        self.enabled = False
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.enabled = True
            print("  [✓] AI Assistant (Gemini) connected!\n")
        except Exception as e:
            print(f"  [!] AI Assistant unavailable: {e}")
            print("  [!] Running in offline mode (no suggestions)\n")

    def analyze(self, source_code, tokens, errors):
        if not self.enabled:
            return None

        # Build a detailed prompt
        token_summary = {}
        for t in tokens:
            token_summary[t.type] = token_summary.get(t.type, 0) + 1

        summary_str = "\n".join([f"  {k}: {v}" for k, v in sorted(token_summary.items())])
        error_str = "\n".join(errors) if errors else "No errors found."

        prompt = f"""You are an expert compiler/code analysis assistant.
A lexical analyzer has just tokenized the following source code.

=== SOURCE CODE ===
{source_code}

=== TOKEN SUMMARY ===
Total tokens: {len(tokens)}
{summary_str}

=== LEXER ERRORS DETECTED ===
{error_str}

Based on the lexical analysis above, provide:

1. **Code Quality Report** (2-3 lines): Is the code well-structured?
2. **Errors & Warnings** (if any): Explain any issues found (missing semicolons, unmatched brackets, unterminated strings, etc.)
3. **Suggestions** (3-5 bullet points): How can the code be improved? (variable naming, best practices, potential bugs)
4. **Optimization Tips** (2-3 bullet points): Performance or readability improvements.
5. **Security Concerns** (if any): Buffer overflows, unsafe functions, etc.

Keep the response concise, clear, and helpful for a student learning compiler design.
"""

        try:
            print("  [*] AI is analyzing your code...\n")
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"  [!] AI Error: {e}"

    def ask_question(self, source_code, question):
        if not self.enabled:
            print("  [!] AI is not available in offline mode.")
            return None

        prompt = f"""You are an expert compiler/code assistant.
Here is the source code being analyzed:

{source_code}

The student asks: {question}

Provide a clear, helpful, and educational answer. Keep it concise.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"  [!] AI Error: {e}"


# ============================================================
#  DISPLAY FUNCTIONS
# ============================================================
def display_tokens(tokens, name="input"):
    print("\n" + "=" * 70)
    print("   LEXICAL ANALYZER OUTPUT")
    print("   Source:", name)
    print("=" * 70)
    print(f"  {'TOKEN TYPE':<16} {'VALUE':<32} {'LOCATION'}")
    print("-" * 70)

    counts = {}
    for t in tokens:
        print(f"  {t.type:<16} {t.value:<32} Ln {t.line} Col {t.column}")
        counts[t.type] = counts.get(t.type, 0) + 1

    print("=" * 70)
    print(f"  TOTAL TOKENS: {sum(counts.values())}")
    print("-" * 70)
    for k, v in sorted(counts.items()):
        print(f"    {k:<20}: {v}")
    print("=" * 70)


def display_errors(errors):
    if errors:
        print("\n" + "!" * 70)
        print("   LEXER ERRORS / WARNINGS")
        print("!" * 70)
        for e in errors:
            print(f"  ⚠  {e}")
        print("!" * 70)


def display_ai_response(response):
    if response:
        print("\n" + "=" * 70)
        print("   🤖 AI ASSISTANT SUGGESTIONS")
        print("=" * 70)
        print(response)
        print("=" * 70)


# ============================================================
#  MAIN PROGRAM
# ============================================================
def main():
    print("\n" + "=" * 58)
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║   LEXICAL ANALYZER WITH AI SUGGESTIONS              ║")
    print("  ║   by Chandresh (RA2311003050021)                    ║")
    print("  ║   Powered by Google Gemini AI                       ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print("=" * 58)

    # Initialize AI
    print("\n  [*] Connecting to AI Assistant...")
    ai = AIAssistant(API_KEY)

    while True:
        print("\n  ┌─────────────────────────────────┐")
        print("  │         MAIN MENU                │")
        print("  ├─────────────────────────────────┤")
        print("  │  [1] Enter code manually         │")
        print("  │  [2] Analyze a file              │")
        print("  │  [3] Run demo with sample code   │")
        print("  │  [4] Ask AI a question           │")
        print("  │  [0] Exit                        │")
        print("  └─────────────────────────────────┘")

        choice = input("\n  Enter choice (0-4): ").strip()
        source = None
        source_name = "input"

        if choice == '1':
            print("\n  Enter your code (type END on a new line to finish):\n")
            lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            source = '\n'.join(lines)
            source_name = "manual input"

        elif choice == '2':
            filename = input("\n  Enter file path: ").strip()
            try:
                with open(filename, 'r') as f:
                    source = f.read()
                source_name = filename
            except FileNotFoundError:
                print(f"\n  [ERROR] File '{filename}' not found!")
                continue

        elif choice == '3':
            source = """#include <stdio.h>

// Calculate factorial
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int num = 5;
    float result = 3.14;
    char *name = "Chandresh";
    char *unterminated = "oops;

    if (num >= 0 && result != 0) {
        printf("Factorial of %d = %d\\n", num, factorial(num));
        printf("Name: %s\\n", name);
        num++;
    }

    /* TODO: Add error handling
       for negative numbers */
    return 0;
}"""
            source_name = "demo_sample.c"
            print("\n  --- SOURCE CODE ---")
            for i, line in enumerate(source.split('\n'), 1):
                print(f"  {i:>3} | {line}")
            print("  --- END SOURCE ---")

        elif choice == '4':
            question = input("\n  Ask AI anything about compilers/code: ").strip()
            if question:
                response = ai.ask_question("", question)
                display_ai_response(response)
            continue

        elif choice == '0':
            print("\n  Goodbye! 👋\n")
            break

        else:
            print("\n  [ERROR] Invalid choice!")
            continue

        if source is not None:
            # --- STEP 1: Tokenize ---
            lexer = Lexer(source)
            tokens = lexer.tokenize()

            # --- STEP 2: Display Tokens ---
            display_tokens(tokens, source_name)

            # --- STEP 3: Display Errors ---
            display_errors(lexer.errors)

            # --- STEP 4: AI Analysis ---
            if ai.enabled:
                get_ai = input("\n  🤖 Get AI suggestions? (y/n): ").strip().lower()
                if get_ai == 'y':
                    response = ai.analyze(source, tokens, lexer.errors)
                    display_ai_response(response)

            # --- STEP 5: Follow-up Questions ---
            while True:
                follow = input("\n  💬 Ask a follow-up question (or press Enter to skip): ").strip()
                if not follow:
                    break
                response = ai.ask_question(source, follow)
                display_ai_response(response)


if __name__ == "__main__":
    main()
