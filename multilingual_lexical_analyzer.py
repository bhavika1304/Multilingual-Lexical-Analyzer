from tabulate import tabulate

class Token:
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

class Lexer:
    def __init__(self, code, language):
        self.code = code
        self.pos = 0
        self.tokens = []
        self.language = language
        self.keywords = self.get_keywords(language)
        self.operators = self.get_operators(language)
        self.current_state = 'start'
        self.current_token = ''

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
            return set(['+', '-', '*', '/', '%', '++', '--', '=', '+=', '-=', '*=', '/=', '%=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '<<', '>>', '~', '>>>'])
        elif language == "c":
            return set(['+', '-', '*', '/', '%', '++', '--', '=', '+=', '-=', '*=', '/=', '%=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '<<', '>>', '~'])
        elif language == "cpp":
            return set(['+', '-', '*', '/', '%', '++', '--', '=', '+=', '-=', '*=', '/=', '%=', '==', '!=', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '<<', '>>', '~', '>>=', '<<=', '->', '->*', '::', '.*'])
        else:
            raise ValueError("Unsupported language")

    def transition(self, char):
        if self.current_state == 'start':
            if char.isalpha() or char == '_':
                self.current_state = 'identifier'
                self.current_token += char
            elif char.isdigit():
                self.current_state = 'number'
                self.current_token += char
            elif char in ('"', "'"):
                self.current_state = 'string'
                self.current_token += char
            elif char in self.get_operators(self.language):
                self.current_state = 'operator'
                self.current_token += char
            elif char.isspace():  # Transition to whitespace state
                self.current_state = 'whitespace'
            else:
                self.current_state = 'symbol'
                self.current_token += char
        elif self.current_state == 'whitespace':  # Whitespace state
            if not char.isspace():  # Transition back to 'start' state when non-whitespace encountered
                self.current_state = 'start'
                self.transition(char)
        elif self.current_state == 'identifier':
            if char.isalnum() or char == '_':
                self.current_token += char
            else:
                if self.current_token in self.keywords:
                    self.tokens.append(Token('Keyword', self.current_token))
                else:
                    self.tokens.append(Token('Identifier', self.current_token))
                self.current_token = ''
                self.current_state = 'start'
                self.transition(char)
        elif self.current_state == 'number':
            if char.isdigit() or char == '.':
                self.current_token += char
            else:
                self.tokens.append(Token('Number', self.current_token))
                self.current_token = ''
                self.current_state = 'start'
                self.transition(char)
        elif self.current_state == 'string':
            self.current_token += char
            if char == self.current_token[0]:
                self.tokens.append(Token('String', self.current_token))
                self.current_token = ''
                self.current_state = 'start'
        elif self.current_state == 'operator':
            if self.current_token + char in self.operators:
                self.current_token += char
            else:
                self.tokens.append(Token('Operator', self.current_token))
                self.current_token = ''
                self.current_state = 'start'
                self.transition(char)
        elif self.current_state == 'symbol':
            if char.isspace() or char in self.get_operators(self.language):
                self.tokens.append(Token('Symbol', self.current_token))
                self.current_token = ''
                self.current_state = 'start'
                self.transition(char)
            else:
                self.current_token += char

    def tokenize(self):
        for char in self.code:
            self.transition(char)
        return self.tokens

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
print(tabulate(token_table, headers=["Token Type", "Value"], tablefmt="grid"))
