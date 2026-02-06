import sys
import re

# ==================== TOKEN TYPES ====================
TOKEN_TYPES = {
    "KEYWORD": [
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "int", "long", "register", "return", "short", "signed", "sizeof", "static",
        "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
        "print", "input", "def", "class", "import", "from", "as", "try", "except",
        "finally", "raise", "with", "yield", "lambda", "pass", "True", "False", "None",
        "and", "or", "not", "in", "is", "elif"
    ]
}

# ==================== TOKEN CLASS ====================
class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __str__(self):
        return f"| {self.type:<16} | {self.value:<30} | Ln {self.line:<4} Col {self.column:<4} |"


# ==================== LEXER CLASS ====================
class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def current_char(self):
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def peek_char(self):
        if self.pos + 1 < len(self.source):
            return self.source[self.pos + 1]
        return None

    def advance(self):
        if self.current_char() == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def skip_whitespace(self):
        while self.current_char() is not None and self.current_char() in ' \t\r':
            self.advance()

    def add_token(self, token_type, value, line, column):
        self.tokens.append(Token(token_type, value, line, column))

    # ---------- NUMBER ----------
    def lex_number(self):
        start_line = self.line
        start_col = self.column
        num_str = ""
        is_float = False

        while self.current_char() is not None and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if is_float:
                    break
                is_float = True
            num_str += self.current_char()
            self.advance()

        token_type = "FLOAT" if is_float else "INTEGER"
        self.add_token(token_type, num_str, start_line, start_col)

    # ---------- IDENTIFIER / KEYWORD ----------
    def lex_identifier(self):
        start_line = self.line
        start_col = self.column
        word = ""

        while self.current_char() is not None and (self.current_char().isalnum() or self.current_char() == '_'):
            word += self.current_char()
            self.advance()

        if word in TOKEN_TYPES["KEYWORD"]:
            self.add_token("KEYWORD", word, start_line, start_col)
        else:
            self.add_token("IDENTIFIER", word, start_line, start_col)

    # ---------- STRING ----------
    def lex_string(self, quote_char):
        start_line = self.line
        start_col = self.column
        string_val = quote_char
        self.advance()  # skip opening quote

        while self.current_char() is not None and self.current_char() != quote_char:
            if self.current_char() == '\\':
                string_val += self.current_char()
                self.advance()
            if self.current_char() is not None:
                string_val += self.current_char()
                self.advance()

        if self.current_char() == quote_char:
            string_val += self.current_char()
            self.advance()

        self.add_token("STRING", string_val, start_line, start_col)

    # ---------- SINGLE-LINE COMMENT ----------
    def lex_single_comment(self):
        start_line = self.line
        start_col = self.column
        comment = ""

        while self.current_char() is not None and self.current_char() != '\n':
            comment += self.current_char()
            self.advance()

        self.add_token("COMMENT", comment, start_line, start_col)

    # ---------- MULTI-LINE COMMENT ----------
    def lex_multi_comment(self):
        start_line = self.line
        start_col = self.column
        comment = "/*"
        self.advance()  # skip '/'
        self.advance()  # skip '*'

        while self.current_char() is not None:
            if self.current_char() == '*' and self.peek_char() == '/':
                comment += "*/"
                self.advance()
                self.advance()
                break
            comment += self.current_char()
            self.advance()

        self.add_token("COMMENT", comment, start_line, start_col)

    # ---------- PREPROCESSOR ----------
    def lex_preprocessor(self):
        start_line = self.line
        start_col = self.column
        directive = ""

        while self.current_char() is not None and self.current_char() != '\n':
            directive += self.current_char()
            self.advance()

        self.add_token("PREPROCESSOR", directive, start_line, start_col)

    # ---------- NEWLINE ----------
    def lex_newline(self):
        start_line = self.line
        start_col = self.column
        self.add_token("NEWLINE", "\\n", start_line, start_col)
        self.advance()

    # ==================== MAIN TOKENIZE ====================
    def tokenize(self):
        multi_char_ops = [
            "==", "!=", "<=", ">=", "&&", "||", "++", "--",
            "+=", "-=", "*=", "/=", "<<", ">>", "->", "**", "//",
        ]

        single_ops = set("+-*/%=<>!&|^~?:@")
        delimiters = set("(){}[];,.")

        while self.pos < len(self.source):
            self.skip_whitespace()
            ch = self.current_char()

            if ch is None:
                break

            # --- Newline ---
            if ch == '\n':
                self.lex_newline()
                continue

            # --- Preprocessor ---
            if ch == '#':
                self.lex_preprocessor()
                continue

            # --- Comments ---
            if ch == '/' and self.peek_char() == '/':
                self.lex_single_comment()
                continue
            if ch == '/' and self.peek_char() == '*':
                self.lex_multi_comment()
                continue
            # Python single-line comment
            if ch == '#':
                self.lex_single_comment()
                continue

            # --- Numbers ---
            if ch.isdigit():
                self.lex_number()
                continue

            # --- Identifiers / Keywords ---
            if ch.isalpha() or ch == '_':
                self.lex_identifier()
                continue

            # --- Strings ---
            if ch in ('"', "'"):
                self.lex_string(ch)
                continue

            # --- Multi-character operators ---
            if self.peek_char() is not None:
                two_char = ch + self.peek_char()
                if two_char in multi_char_ops:
                    self.add_token("OPERATOR", two_char, self.line, self.column)
                    self.advance()
                    self.advance()
                    continue

            # --- Single-character operators ---
            if ch in single_ops:
                self.add_token("OPERATOR", ch, self.line, self.column)
                self.advance()
                continue

            # --- Delimiters ---
            if ch in delimiters:
                self.add_token("DELIMITER", ch, self.line, self.column)
                self.advance()
                continue

            # --- Unknown ---
            self.add_token("UNKNOWN", ch, self.line, self.column)
            self.advance()

        return self.tokens


# ==================== DISPLAY RESULTS ====================
def display_tokens(tokens, source_name="input"):
    print()
    print("+" + "=" * 68 + "+")
    print("|" + "  LEXICAL ANALYZER OUTPUT".center(68) + "|")
    print("|" + f"  Source: {source_name}".center(68) + "|")
    print("+" + "=" * 68 + "+")
    print(f"| {'TOKEN TYPE':<16} | {'VALUE':<30} | {'LOCATION':<15} |")
    print("+" + "-" * 68 + "+")

    # Count by type
    type_count = {}

    for token in tokens:
        if token.type == "NEWLINE":
            continue  # skip newline tokens in display
        print(token)
        type_count[token.type] = type_count.get(token.type, 0) + 1

    print("+" + "=" * 68 + "+")
    print(f"| {'TOTAL TOKENS:':<16}   {sum(type_count.values()):<47} |")
    print("+" + "-" * 68 + "+")

    # Summary
    print(f"| {'TOKEN SUMMARY':<66} |")
    print("+" + "-" * 68 + "+")
    for ttype, count in sorted(type_count.items()):
        print(f"|   {ttype:<20} : {count:<43} |")
    print("+" + "=" * 68 + "+")


# ==================== MAIN ====================
def main():
    if len(sys.argv) >= 2:
        # ---------- FILE MODE ----------
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f:
                source = f.read()
            print(f"\n[*] Reading file: {filename}")
        except FileNotFoundError:
            print(f"\n[ERROR] File '{filename}' not found!")
            sys.exit(1)

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        display_tokens(tokens, filename)

    else:
        # ---------- INTERACTIVE MODE ----------
        print()
        print("+" + "=" * 52 + "+")
        print("|" + "  LEXICAL ANALYZER - Python Edition".center(52) + "|")
        print("|" + "  by Chandresh (RA2311003050021)".center(52) + "|")
        print("+" + "=" * 52 + "+")
        print()
        print("  Choose an option:")
        print("  [1] Enter code manually")
        print("  [2] Analyze a file")
        print("  [3] Run demo with sample code")
        print("  [0] Exit")
        print()

        choice = input("  Enter choice (0-3): ").strip()

        if choice == '1':
            print("\n  Enter your code (type 'END' on a new line to finish):\n")
            lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            source = '\n'.join(lines)

            lexer = Lexer(source)
            tokens = lexer.tokenize()
            display_tokens(tokens, "manual input")

        elif choice == '2':
            filename = input("\n  Enter file path: ").strip()
            try:
                with open(filename, 'r') as f:
                    source = f.read()
            except FileNotFoundError:
                print(f"\n  [ERROR] File '{filename}' not found!")
                sys.exit(1)

            lexer = Lexer(source)
            tokens = lexer.tokenize()
            display_tokens(tokens, filename)

        elif choice == '3':
            # Demo with sample C code
            sample_code = '''#include <stdio.h>

// Sample program
int main() {
    int x = 10;
    float pi = 3.14;
    char *msg = "Hello, World!";

    if (x >= 5 && pi != 0) {
        printf("%s\\n", msg);
        x++;
    }

    /* Multi-line
       comment */
    return 0;
}'''
            print("\n  [*] Running demo with sample C code...\n")
            print("  --- SOURCE CODE ---")
            for i, line in enumerate(sample_code.split('\n'), 1):
                print(f"  {i:>3} | {line}")
            print("  --- END SOURCE ---")

            lexer = Lexer(sample_code)
            tokens = lexer.tokenize()
            display_tokens(tokens, "demo_sample.c")

        elif choice == '0':
            print("\n  Goodbye!\n")
            sys.exit(0)

        else:
            print("\n  [ERROR] Invalid choice!")
            sys.exit(1)


if __name__ == "__main__":
    main()