from tabulate import tabulate

class Token:
    def _init_(self, token_type, value):
        self.token_type = token_type
        self.value = value

class Lexer:
    def _init_(self, code, language):
        self.code = code
        self.tokens = []
        self.errors = []  # List to store error messages
        self.language = language
        self.keywords = self.get_keywords(language)
        self.operators = self.get_operators(language)
        self.current_state = 'start'
        self.current_token = ''
        self.string_open_char = None  # Track opening char for strings
        self.line_number = 1  # Track line number for error reporting
        self.position = 0  # Track character position for error reporting

    def get_keywords(self, language):
        if language == "java":
            return set(['abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 'if', 'implements', 'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package', 'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile', 'while'])
        elif language == "c":
            return set(['auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'inline', 'int', 'long', 'register', 'restrict', 'return', 'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'])
        elif language == "cpp":
            return set(['alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor', 'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t', 'class', 'compl', 'concept', 'const', 'constexpr', 'const_cast', 'continue', 'co_await', 'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend', 'goto', 'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 'private', 'protected', 'public', 'reflexpr', 'register', 'reinterpret_cast', 'requires', 'return', 'short', 'signed', 'sizeof', 'static', 'static_assert', 'static_cast', 'struct', 'switch', 'synchronized', 'template', 'this', 'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq'])
        else:
            raise ValueError("Unsupported language")

    def get_operators(self, language):
        if language == "java":
            return set(['+', '-', '', '/', '%', '++', '--', '=', '+=', '-=', '=', '/=', '%=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '<<', '>>', '~', '>>>'])
        elif language == "c":
            return set(['+', '-', '', '/', '%', '++', '--', '=', '+=', '-=', '=', '/=', '%=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '<<', '>>', '~'])
        elif language == "cpp":
            return set(['+', '-', '', '/', '%', '++', '--', '=', '+=', '-=', '=', '/=', '%=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '<<', '>>', '~', '>>=', '<<=', '->', '->', '::', '.'])
        else:
            raise ValueError("Unsupported language")

    def add_token(self, token_type):
        if self.current_token:
            if token_type == 'Identifier' and self.current_token in self.get_standard_functions():
                self.tokens.append(Token('Standard Function', self.current_token))
            else:
                self.tokens.append(Token(token_type, self.current_token))
        self.current_token = ''

    def report_error(self, message):
        self.errors.append(f"Error at line {self.line_number}, position {self.position}: {message}")

    def transition(self, char):
        self.position += 1  # Increment position for each character
        if char == '\n':
            self.line_number += 1
            self.position = 0  # Reset position for new line

        state_actions = {
            'start': self.handle_start,
            'preprocessor': self.handle_preprocessor,
            'header_file': self.handle_header_file,
            'identifier': self.handle_identifier,
            'number': self.handle_number,
            'string': self.handle_string,
            'operator': self.handle_operator,
            'comment': self.handle_comment,
        }

        # Call the appropriate handling method based on current state
        if self.current_state in state_actions:
            state_actions[self.current_state](char)
        else:
            self.report_error(f"Invalid state '{self.current_state}'")

    def handle_start(self, char):
        if char == '#':
            self.current_state = 'preprocessor'
            self.current_token += char
        elif char.isalpha() or char == '_':
            self.current_state = 'identifier'
            self.current_token += char
        elif char.isdigit():
            self.current_state = 'number'
            self.current_token += char
        elif char in ('"', "'"):
            self.current_state = 'string'
            self.string_open_char = char
            self.current_token += char
        elif char in self.operators:
            self.current_state = 'operator'
            self.current_token += char
        elif char in '(){};,.':
            self.add_token('Symbol')
            self.tokens.append(Token('Symbol', char))
        elif char.isspace():
            pass  # Ignore whitespace in start state
        elif char == '/':
            self.current_state = 'comment'  # Start of comment
            self.current_token += char
        else:
            self.report_error(f"Invalid character '{char}'")

    def handle_comment(self, char):
        if char == '\n':
            self.current_state = 'start'  # End of comment
        else:
            self.current_token += char  # Collect comment content

    def handle_preprocessor(self, char):
        if self.current_token == '#include':
            if char in ('"', '<'):
                self.current_token += char
                self.current_state = 'header_file'
            else:
                self.current_token += char
        elif char.isalnum() or char == '_':
            self.current_token += char
        elif char.isspace():
            self.add_token('Preprocessor')  # Add the directive
            self.current_state = 'start'  # Reset state to start
        else:
            self.current_token += char  # Handle symbols in preprocessing

    def handle_header_file(self, char):
        if char.isalnum() or char in ('_', '.', '/', '\\'):
            self.current_token += char
        elif char == '"':
            self.add_token('Header')  # User-defined header
            self.current_state = 'start'
        elif char == '>':
            self.add_token('Header')  # System header
            self.current_state = 'start'
        else:
            self.current_token += char  # Handle unexpected characters

    def handle_identifier(self, char):
        if char.isalnum() or char == '_':
            self.current_token += char
        else:
            if self.current_token in self.keywords:
                self.add_token('Keyword')
            elif self.current_token[0].isdigit():  # Invalid identifier
                self.report_error(f"Invalid identifier '{self.current_token}'")
            else:
                self.add_token('Identifier')
            self.current_state = 'start'
            self.transition(char)

    def handle_number(self, char):
        if char.isdigit() or char == '.':
            self.current_token += char
        else:
            self.add_token('Number')
            self.current_state = 'start'
            self.transition(char)

    def handle_string(self, char):
        self.current_token += char
        if char == self.string_open_char:
            self.add_token('String')
            self.current_state = 'start'
            self.string_open_char = None  # Reset the string tracker
        elif self.position == len(self.code):  # End of code without closing quote
            self.report_error("Unterminated string literal")

    def handle_operator(self, char):
        if self.current_token + char in self.operators:
            self.current_token += char
        else:
            self.add_token('Operator')
            self.current_state = 'start'
            self.transition(char)

    def tokenize(self):
        for char in self.code:
            self.transition(char)
        # Add any remaining token after the loop
        if self.current_token:
            if self.current_state == 'identifier':
                if self.current_token in self.keywords:
                    self.add_token('Keyword')
                elif self.current_token[0].isdigit():  # Invalid identifier
                    self.report_error(f"Invalid identifier '{self.current_token}'")
                else:
                    self.add_token('Identifier')
            elif self.current_state == 'number':
                self.add_token('Number')
            elif self.current_state == 'string':
                self.add_token('String')
            elif self.current_state == 'operator':
                self.add_token('Operator')
            else:
                self.add_token('Symbol')

        return self.tokens

    def get_standard_functions(self):
        return set(['printf', 'scanf', 'malloc', 'free', 'return', 'exit'])  # Add more as needed

def generate_token_table(tokens):
    table = []
    for token in tokens:
        table.append([token.token_type, token.value])
    return table

def detect_language(file_path):
    if file_path.endswith(".java"):
        return "java"
    elif file_path.endswith(".c"):
        return "c"
    elif file_path.endswith(".cpp"):
        return "cpp"
    else:
        raise ValueError("Unsupported file type")

# Get file path input from the user
file_path = input("Enter the path to your code file:\n")

# Read the content of the file
with open(file_path, 'r') as file:
    code = file.read()

language = detect_language(file_path)
lexer = Lexer(code, language)
tokens = lexer.tokenize()
token_table = generate_token_table(tokens)

# Print token table
print(tabulate(token_table, headers=["Token Type", "Value"], tablefmt="grid"))

# Print any errors encountered
if lexer.errors:
    print("\nLexical Errors:")
    for error in lexer.errors:
        print(error)
