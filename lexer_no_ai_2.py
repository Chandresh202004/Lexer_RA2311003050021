#!/usr/bin/env python3
"""
Simple Lexical Analyzer (Lexer) - No AI/API Key Usage
Author: Chandresh (RA2311003050021)
Description: A clean, simple lexer implementation for tokenizing code
"""

import sys

# ==================== TOKEN TYPES ====================
KEYWORDS = [
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if",
    "int", "long", "register", "return", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
    "print", "input", "def", "class", "import", "from", "as", "try", "except",
    "finally", "raise", "with", "yield", "lambda", "pass", "True", "False", "None",
    "and", "or", "not", "in", "is", "elif"
]


# ==================== TOKEN CLASS ====================
class Token:
    """Represents a single token with type, value, and position"""
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __str__(self):
        return f"| {self.type:<15} | {self.value:<28} | Line {self.line:<4} Col {self.column:<4} |"


# ==================== LEXER CLASS ====================
class Lexer:
    """Simple lexical analyzer for tokenizing source code"""
    
    def __init__(self, source_code):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def current_char(self):
        """Return the current character or None if at end"""
        if self.position < len(self.source):
            return self.source[self.position]
        return None

    def peek_char(self):
        """Look at the next character without consuming it"""
        if self.position + 1 < len(self.source):
            return self.source[self.position + 1]
        return None

    def advance(self):
        """Move to the next character and update position tracking"""
        if self.current_char() == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def skip_whitespace(self):
        """Skip spaces, tabs, and carriage returns"""
        while self.current_char() in ' \t\r':
            self.advance()

    def add_token(self, token_type, value, line, column):
        """Add a new token to the token list"""
        self.tokens.append(Token(token_type, value, line, column))

    def tokenize_number(self):
        """Tokenize integer or floating-point numbers"""
        start_line = self.line
        start_col = self.column
        number = ""
        has_decimal = False

        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if has_decimal:
                    break  # Multiple decimal points
                has_decimal = True
            number += self.current_char()
            self.advance()

        token_type = "FLOAT" if has_decimal else "INTEGER"
        self.add_token(token_type, number, start_line, start_col)

    def tokenize_identifier(self):
        """Tokenize identifiers and keywords"""
        start_line = self.line
        start_col = self.column
        identifier = ""

        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            identifier += self.current_char()
            self.advance()

        # Check if it's a keyword
        if identifier in KEYWORDS:
            self.add_token("KEYWORD", identifier, start_line, start_col)
        else:
            self.add_token("IDENTIFIER", identifier, start_line, start_col)

    def tokenize_string(self, quote_type):
        """Tokenize string literals (single or double quoted)"""
        start_line = self.line
        start_col = self.column
        string_value = quote_type
        self.advance()  # Skip opening quote

        while self.current_char() and self.current_char() != quote_type:
            if self.current_char() == '\\':
                string_value += self.current_char()
                self.advance()
                if self.current_char():
                    string_value += self.current_char()
                    self.advance()
            elif self.current_char():
                string_value += self.current_char()
                self.advance()

        if self.current_char() == quote_type:
            string_value += self.current_char()
            self.advance()

        self.add_token("STRING", string_value, start_line, start_col)

    def tokenize_comment(self):
        """Tokenize single-line comments (//)"""
        start_line = self.line
        start_col = self.column
        comment = ""

        while self.current_char() and self.current_char() != '\n':
            comment += self.current_char()
            self.advance()

        self.add_token("COMMENT", comment, start_line, start_col)

    def tokenize_multi_line_comment(self):
        """Tokenize multi-line comments (/* ... */)"""
        start_line = self.line
        start_col = self.column
        comment = "/*"
        self.advance()  # Skip '/'
        self.advance()  # Skip '*'

        while self.current_char():
            if self.current_char() == '*' and self.peek_char() == '/':
                comment += "*/"
                self.advance()
                self.advance()
                break
            comment += self.current_char()
            self.advance()

        self.add_token("COMMENT", comment, start_line, start_col)

    def tokenize_preprocessor(self):
        """Tokenize preprocessor directives (#include, #define, etc.)"""
        start_line = self.line
        start_col = self.column
        directive = ""

        while self.current_char() and self.current_char() != '\n':
            directive += self.current_char()
            self.advance()

        self.add_token("PREPROCESSOR", directive, start_line, start_col)

    def tokenize(self):
        """Main tokenization method"""
        # Define operators and delimiters
        multi_char_operators = [
            "==", "!=", "<=", ">=", "&&", "||", "++", "--",
            "+=", "-=", "*=", "/=", "<<", ">>", "->", "**", "//"
        ]
        single_char_operators = set("+-*/%=<>!&|^~?:@")
        delimiters = set("(){}[];,.")

        while self.position < len(self.source):
            self.skip_whitespace()
            char = self.current_char()

            if char is None:
                break

            # Handle newlines
            if char == '\n':
                self.advance()
                continue

            # Handle preprocessor directives
            if char == '#':
                self.tokenize_preprocessor()
                continue

            # Handle comments
            if char == '/' and self.peek_char() == '/':
                self.tokenize_comment()
                continue
            
            if char == '/' and self.peek_char() == '*':
                self.tokenize_multi_line_comment()
                continue

            # Handle numbers
            if char.isdigit():
                self.tokenize_number()
                continue

            # Handle identifiers and keywords
            if char.isalpha() or char == '_':
                self.tokenize_identifier()
                continue

            # Handle strings
            if char in ('"', "'"):
                self.tokenize_string(char)
                continue

            # Handle multi-character operators
            if self.peek_char():
                two_char = char + self.peek_char()
                if two_char in multi_char_operators:
                    self.add_token("OPERATOR", two_char, self.line, self.column)
                    self.advance()
                    self.advance()
                    continue

            # Handle single-character operators
            if char in single_char_operators:
                self.add_token("OPERATOR", char, self.line, self.column)
                self.advance()
                continue

            # Handle delimiters
            if char in delimiters:
                self.add_token("DELIMITER", char, self.line, self.column)
                self.advance()
                continue

            # Handle unknown characters
            self.add_token("UNKNOWN", char, self.line, self.column)
            self.advance()

        return self.tokens


# ==================== DISPLAY FUNCTIONS ====================
def display_tokens(tokens, source_name="input"):
    """Display tokens in a formatted table"""
    print()
    print("=" * 70)
    print("  LEXICAL ANALYZER OUTPUT".center(70))
    print(f"  Source: {source_name}".center(70))
    print("=" * 70)
    print(f"| {'TOKEN TYPE':<15} | {'VALUE':<28} | {'LOCATION':<18} |")
    print("-" * 70)

    # Count tokens by type
    token_counts = {}

    for token in tokens:
        print(token)
        token_counts[token.type] = token_counts.get(token.type, 0) + 1

    print("=" * 70)
    print(f"  TOTAL TOKENS: {sum(token_counts.values())}")
    print("-" * 70)

    # Display token summary
    print("  TOKEN SUMMARY:")
    for token_type, count in sorted(token_counts.items()):
        print(f"    {token_type:<20}: {count}")
    print("=" * 70)
    print()


# ==================== MAIN FUNCTION ====================
def main():
    """Main program entry point"""
    print()
    print("=" * 60)
    print("  SIMPLE LEXICAL ANALYZER (No AI/API)".center(60))
    print("  by Chandresh (RA2311003050021)".center(60))
    print("=" * 60)
    print()

    # Check if file is provided as command-line argument
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as file:
                source_code = file.read()
            print(f"[*] Reading file: {filename}\n")
            
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            display_tokens(tokens, filename)
            
        except FileNotFoundError:
            print(f"[ERROR] File '{filename}' not found!")
            sys.exit(1)
    else:
        # Interactive mode
        print("Choose an option:")
        print("  [1] Enter code manually")
        print("  [2] Analyze a file")
        print("  [3] Run demo with sample code")
        print("  [0] Exit")
        print()

        choice = input("Enter choice (0-3): ").strip()

        if choice == '1':
            print("\nEnter your code (type 'END' on a new line to finish):\n")
            lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            source_code = '\n'.join(lines)

            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            display_tokens(tokens, "manual input")

        elif choice == '2':
            filename = input("\nEnter file path: ").strip()
            try:
                with open(filename, 'r') as file:
                    source_code = file.read()
                
                lexer = Lexer(source_code)
                tokens = lexer.tokenize()
                display_tokens(tokens, filename)
                
            except FileNotFoundError:
                print(f"\n[ERROR] File '{filename}' not found!")
                sys.exit(1)

        elif choice == '3':
            # Demo with sample code
            sample_code = '''#include <stdio.h>

// Simple C program
int main() {
    int x = 10;
    float pi = 3.14159;
    char *message = "Hello, World!";

    if (x >= 5 && pi != 0.0) {
        printf("%s\\n", message);
        x++;
    }

    /* This is a
       multi-line comment */
    return 0;
}'''
            print("\n[*] Running demo with sample C code...\n")
            print("--- SOURCE CODE ---")
            for i, line in enumerate(sample_code.split('\n'), 1):
                print(f"  {i:>3} | {line}")
            print("--- END SOURCE ---")

            lexer = Lexer(sample_code)
            tokens = lexer.tokenize()
            display_tokens(tokens, "demo_sample.c")

        elif choice == '0':
            print("\nGoodbye!\n")
            sys.exit(0)

        else:
            print("\n[ERROR] Invalid choice!")
            sys.exit(1)


if __name__ == "__main__":
    main()
