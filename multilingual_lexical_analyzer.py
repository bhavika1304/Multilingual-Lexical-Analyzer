from tabulate import tabulate

class Token:
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

class Lexer:
    def __init__(self, code, language):
        self.code = code
        self.tokens = []
        self.errors = []
        self.language = language
        self.keywords = self.get_keywords(language)
        self.operators = self.get_operators(language)
        self.system_io_functions = self.get_system_io_functions()  # Functions that can follow `System.out`
        self.standard_classes = self.get_standard_classes()  # To recognize Java standard classes like StringBuilder
        self.current_state = 'start'
        self.current_token = ''
        self.previous_token = ''  # To track previous token for `System.out`
        self.string_open_char = None
        self.line_number = 1
        self.position = 0
        self.is_package_import = False  # To track if we are in a package import sequence

    def get_keywords(self, language):
        if language == "java":
            return set(['abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extends', 'final', 'finally', 'float', 'for', 'if', 'implements', 'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new', 'package', 'private', 'protected', 'public', 'return', 'short', 'static', 'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 'void', 'volatile', 'while'])
        else:
            raise ValueError("Unsupported language")

    def get_operators(self, language):
        if language == "java":
            return set(['+', '-', '*', '/', '%', '++', '--', '=', '+=', '-=', '*=', '/=', '%=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '<<', '>>', '~', '>>>'])
        else:
            raise ValueError("Unsupported language")

    def get_system_io_functions(self):
        # Functions that can follow `System.out`
        return {'println', 'print', 'flush'}

    def get_standard_classes(self):
        # Recognize common Java standard classes like String, StringBuilder, Scanner, etc.
        return {'StringBuilder', 'String', 'Scanner', 'System'}

    def add_token(self, token_type):
        if self.current_token:
            self.tokens.append(Token(token_type, self.current_token))
        self.current_token = ''

    def report_error(self, message):
        self.errors.append(f"Error at line {self.line_number}, position {self.position}: {message}")

    def transition(self, char):
        self.position += 1
        if char == '\n':
            self.line_number += 1
            self.position = 0

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
        elif char in '(){};,:[]':  # Updated to recognize valid symbols
            self.add_token('Symbol')
            self.tokens.append(Token('Symbol', char))
        elif char.isspace():
            pass  # Ignore whitespace
        elif char == '/':
            self.current_state = 'comment'
            self.current_token += char
        else:
            self.report_error(f"Invalid character '{char}'")

    def handle_comment(self, char):
        if char == '\n':
            self.current_state = 'start'
        else:
            self.current_token += char

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
            self.add_token('Preprocessor')
            self.current_state = 'start'
        else:
            self.current_token += char

    def handle_header_file(self, char):
        if char.isalnum() or char in ('_', '.', '/', '\\'):
            self.current_token += char
        elif char == '"':
            self.add_token('Header')
            self.current_state = 'start'
        elif char == '>':
            self.add_token('Header')
            self.current_state = 'start'
        else:
            self.current_token += char

    def handle_identifier(self, char):
        if char == '.':
            if self.current_token:
                self.current_token += char  # Combine identifiers like java.util.Scanner or System.out
        elif self.previous_token == 'System.out' and self.current_token in self.system_io_functions:
            # Combine System.out.println or similar
            combined_token = f"System.out.{self.current_token}"
            self.tokens.pop()  # Remove the System.out token from tokens
            self.tokens.append(Token('System Input/Output', combined_token))  # Add combined token
            self.previous_token = ''
            self.current_token = ''
        elif char.isalnum() or char == '_':
            self.current_token += char
        else:
            # Check if it's a class name, method name, or standard class
            if self.current_token in self.standard_classes:
                self.add_token('Class Name')
            elif self.current_token[0].isupper():
                self.add_token('Class Name')  # Assuming identifiers starting with uppercase are classes
            elif self.current_token in self.keywords:
                self.add_token('Keyword')
            elif self.current_token[0].islower() and char == '(':
                self.add_token('Method Name')  # Methods usually start with lowercase
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
            self.string_open_char = None
        elif self.position == len(self.code):
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
        if self.current_token:
            if self.previous_token == 'System.out' and self.current_token in self.system_io_functions:
                combined_token = f"System.out.{self.current_token}"
                self.tokens.pop()  # Remove the `System.out` token
                self.tokens.append(Token('System Input/Output', combined_token))  # Add combined token
            elif self.current_token in self.standard_classes:
                self.add_token('Class Name')
            elif self.current_token in self.keywords:
                self.add_token('Keyword')
            elif self.current_token[0].isdigit():
                self.report_error(f"Invalid identifier '{self.current_token}'")
            else:
                self.add_token('Identifier')
        elif self.current_state == 'number':
            self.add_token('Number')
        elif self.current_state == 'string':
            self.add_token('String')
        elif self.current_state == 'operator':
            self.add_token('Operator')

        return self.tokens

    def get_standard_functions(self):
        return set(['System.out.println', 'printf', 'scanf', 'malloc', 'free', 'return', 'exit'])

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
