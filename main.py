import re
import io
from contextlib import redirect_stdout

# global flag: set to True to print production rules
PRINT_PRODUCTIONS = True

# maximum number of instructions and program counter
MAX_INSTR = 1000
instructions = [None] * MAX_INSTR
instr_ptr = 1   # next instruction index

def emit(op, *args, comment=None):
    global instr_ptr
    parts = [f"{instr_ptr:4d}", f"{op:<6}"]
    if args:
        parts.append(" ".join(str(a) for a in args))
    if comment:
        parts.append(f"; {comment}")
    instructions[instr_ptr-1] = "  ".join(parts)
    instr_ptr += 1

def print_assembly():
    print("\nAssembly Listing:")
    for idx in range(instr_ptr - 1):
        raw = instructions[idx]
        if not raw:
            continue
        parts = raw.strip().split(None, 2)
        _, op = parts[0], parts[1]
        tail = parts[2] if len(parts) > 2 else ""
        # separate args from comment
        if ";" in tail:
            args, comment = tail.split(";", 1)
            comment = comment.strip()
        else:
            args, comment = tail, ""
        args = args.strip()
        print(f"[{idx+1:2d}]   {op:<7}{args:<12}" + (f"  ; {comment}" if comment else ""))

# global memory address counter
Memory_Address = 10000

# symbol table: key = identifier name, value = (memory address, type)
symbol_table = {}

def is_declared(lexeme):
    return lexeme in symbol_table

def insert_identifier(lexeme, var_type):
    global Memory_Address
    if is_declared(lexeme):
        raise Exception(f"Semantic Error: Identifier '{lexeme}' is already declared.")
    symbol_table[lexeme] = (Memory_Address, var_type)
    Memory_Address += 1

def print_symbol_table():
    print("\nSymbol Table:")
    print("Identifier      Memory Address     Type")
    print("----------------------------------------")
    for lexeme, (addr, var_type) in symbol_table.items():
        print(f"{lexeme:<15}{addr:<18}{var_type}")

# pr(rule): Prints a production rule if PRINT_PRODUCTIONS is enabled
def pr(rule):
    if PRINT_PRODUCTIONS:
        print(rule)

# token class: Stores token type, lexeme, and optionally a line number
class Token:
    def __init__(self, token_type, lexeme, line=None):
        self.token_type = token_type
        self.lexeme = lexeme
        self.line = line
    def __str__(self):
        return f"{self.token_type:<10} {self.lexeme}"

# Global definitions: Sets for keywords, operators, separators and regex patterns
KEYWORDS = {
    "while", "endwhile", "if", "endif", "else",
    "integer", "boolean", "true", "false",
    "return", "print", "scan"
}
OPERATORS = {"=", "+", "-", "*", "/", "<", "<=", ">", ">=", "==", "!=", "=>"}
SEPARATORS = {"(", ")", "{", "}", ";", ",", "[", "]", "$$"}
token_pattern = r"\$\$|=>|[a-zA-Z][a-zA-Z0-9_]*|[0-9]+\.[0-9]+|[0-9]+|[=+\-*/<>!]=?|[();,{}]"
COMMENT_RE = re.compile(r"\[\*.*?\*\]", re.DOTALL)

# lexer: Tokenizes the input source code and returns a list of tokens
def lexer(source_code):
    source_code = re.sub(COMMENT_RE, "", source_code)
    tokens = []
    for word in re.findall(token_pattern, source_code):
        if word in KEYWORDS:
            tokens.append(Token("keyword", word))
        elif word in OPERATORS:
            tokens.append(Token("operator", word))
        elif word in SEPARATORS:
            tokens.append(Token("separator", word))
        elif re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*", word):
            tokens.append(Token("identifier", word))
        elif re.fullmatch(r"[0-9]+", word):
            tokens.append(Token("integer", word))
        elif re.fullmatch(r"[0-9]+\.[0-9]+", word):
            tokens.append(Token("real", word))
        else:
            tokens.append(Token("unknown", word))
    return tokens

# Parser class: Implements a recursive descent parser for Rat25S
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = tokens[0] if tokens else None

    def advance(self):
        self.current_token_index += 1
        self.current_token = (
            self.tokens[self.current_token_index]
            if self.current_token_index < len(self.tokens) else None
        )

    def match(self, expected_type, expected_lexeme=None):
        if (self.current_token is not None and
            self.current_token.token_type == expected_type and
            (expected_lexeme is None or self.current_token.lexeme == expected_lexeme)):
            print(f"Token: {self.current_token.token_type.capitalize()} Lexeme: {self.current_token.lexeme}")
            self.advance()
        else:
            msg = f"Expected {expected_type}"
            if expected_lexeme:
                msg += f" '{expected_lexeme}'"
            msg += f", found {self.current_token}"
            if self.current_token_index == 0 and expected_lexeme == "$$":
                msg += ". The program must begin with the '$$' delimiter."
            self.error(msg)

    def error(self, message):
        full_msg = ("Syntax Error: " + message +
                    f" (at token index {self.current_token_index}: {self.current_token})")
        print(full_msg)
        raise Exception(full_msg)

    def parse_rat25s(self):
        print("<Rat25S> -> $$ <Opt Declaration List> $$ <Statement List> $$")
        self.match("separator", "$$")
        while (self.current_token
               and self.current_token.token_type == "separator"
               and self.current_token.lexeme == "$$"):
            self.match("separator", "$$")
        self.opt_declaration_list()
        if (self.current_token
            and self.current_token.token_type == "separator"
            and self.current_token.lexeme == "$$"):
            self.match("separator", "$$")
        self.statement_list(terminators={"$$"})
        self.match("separator", "$$")
        print("\nParsing complete.\n")

    def opt_declaration_list(self):
        pr("<Opt Declaration List> -> <Declaration List> | ε")
        if (self.current_token
            and self.current_token.token_type == "keyword"
            and self.current_token.lexeme in {"integer", "boolean"}):
            self.declaration_list()
        else:
            pr("<Opt Declaration List> -> ε")

    def declaration_list(self):
        pr("<Declaration List> -> <Declaration> ; | <Declaration> ; <Declaration List>")
        self.declaration()
        self.match("separator", ";")
        while (self.current_token and self.current_token.token_type == "keyword"
               and self.current_token.lexeme in {"integer", "boolean", "real"}):
            self.declaration()
            self.match("separator", ";")

    def declaration(self):
        print("<Declaration> -> <Qualifier> <IDs>")
        var_type = self.current_token.lexeme
        self.qualifier()
        self.ids(var_type)

    def qualifier(self):
        print("<Qualifier> -> integer | boolean")
        if self.current_token.lexeme in ["integer", "boolean"]:
            self.match("keyword")
        else:
            self.error("Expected type qualifier")

    def ids(self, var_type=None):
        pr("<IDs> -> <Identifier> | <Identifier> , <IDs>")
        while True:
            if (self.current_token and
                self.current_token.token_type == "identifier"):
                name = self.current_token.lexeme
                if var_type:
                    insert_identifier(name, var_type)
                elif not is_declared(name):
                    self.error(f"Semantic Error: Identifier '{name}' used without declaration.")
                self.match("identifier")
            else:
                self.error("Expected identifier")

            if (self.current_token and
                self.current_token.token_type == "separator" and
                self.current_token.lexeme == ","):
                self.match("separator", ",")
            else:
                break

    def statement_list(self, terminators):
        pr("<Statement List> -> <Statement> | <Statement> <Statement List>")
        while self.current_token and self.current_token.lexeme not in terminators:
            self.statement()

    def statement(self):
        if self.current_token.token_type == "separator" and self.current_token.lexeme == "{":
            self.compound_statement()
        elif self.current_token.token_type == "keyword":
            if self.current_token.lexeme == "if":
                self.if_statement()
            elif self.current_token.lexeme == "while":
                self.while_statement()
            elif self.current_token.lexeme == "return":
                self.return_statement()
            elif self.current_token.lexeme == "print":
                self.print_statement()
            elif self.current_token.lexeme == "scan":
                self.scan_statement()
            else:
                self.error(f"Unexpected keyword in statement: {self.current_token.lexeme}")
        elif self.current_token.token_type == "identifier":
            self.assignment()
        else:
            self.error(f"Unexpected token in statement: {self.current_token}")

    def compound_statement(self):
        pr("<Compound> -> { <Statement List> }")
        self.match("separator", "{")
        self.statement_list(terminators={"}"})
        self.match("separator", "}")

    def assignment(self):
        pr("<Assign> -> <Identifier> = <Expression> ;")
        # capture variable name before matching
        var_name = self.current_token.lexeme
        self.match("identifier")
        self.match("operator", "=")
        self.expression()
        self.match("separator", ";")
        # codegen: store result into variable
        emit("STO", var_name, comment=f"{var_name} = <expr>")

    def scan_statement(self):
        pr("<Scan> -> scan ( <IDs> ) ;")
        self.match("keyword", "scan")
        self.match("separator", "(")
        scanned_name = self.current_token.lexeme
        self.match("identifier")
        self.match("separator", ")")
        self.match("separator", ";")
        # stack‑machine: read integer input then store
        addr = symbol_table[scanned_name][0]
        emit("SIN")
        emit("POPM", addr)

    def print_statement(self):
        pr("<Print> -> print ( <Expression> ) ;")
        self.match("keyword", "print")
        self.match("separator", "(")
        self.expression()
        self.match("separator", ")")
        self.match("separator", ";")
        # stack‑machine: pop & print top of stack
        emit("SOUT")

    def while_statement(self):
        pr("<While> -> while ( <Condition> ) <Statement List> endwhile")
        self.match("keyword", "while")
        self.match("separator", "(")
        self.condition()
        self.match("separator", ")")

        # loop entry label
        start_label = instr_ptr
        emit("LABEL")

        # placeholder for exit jump
        patch_slot = instr_ptr
        emit("JMP0", 0)

        # loop body
        self.match("separator", "{")
        self.statement_list(terminators={"}"})
        self.match("separator", "}")

        # jump back to top
        emit("JMP", start_label)

        # patch the exit target
        exit_target = instr_ptr
        instructions[patch_slot-1] = f"{patch_slot} JMP0 {exit_target}"

        self.match("keyword", "endwhile")

    def if_statement(self):
        pr("<If> -> if ( <Condition> ) <Statement> (else <Statement>)? endif")
        self.match("keyword", "if")
        self.match("separator", "(")
        self.condition()
        self.match("separator", ")")
        self.statement()
        if self.current_token and self.current_token.lexeme == "else":
            self.match("keyword", "else")
            self.statement()
        self.match("keyword", "endif")

    def return_statement(self):
        pr("<Return> -> return (<Expression>)? ;")
        self.match("keyword", "return")
        if self.current_token and not (self.current_token.lexeme == ";"):
            self.expression()
        self.match("separator", ";")

    def condition(self):
        pr("<Condition> -> <Expression> <Relop> <Expression>")
        self.expression()
        relop = self.current_token.lexeme
        self.match("operator")
        self.expression()
        # codegen: comparison
        cmp_map = {
            "<": "CMP_LT", ">": "CMP_GT",
            "==": "CMP_EQ","!=": "CMP_NE",
            "<=": "CMP_LE", ">=": "CMP_GE"
        }
        emit(cmp_map[relop], comment=f"compare {relop}")

    def expression(self):
        pr("<Expression> -> <Term> { (+|-) <Term> }")
        # literal integer
        if self.current_token.token_type == "integer":
            val = int(self.current_token.lexeme)
            self.match("integer")
            emit("PUSHI", val)

        # identifier
        elif self.current_token.token_type == "identifier":
            name = self.current_token.lexeme
            if not is_declared(name):
                self.error(f"Semantic Error: Identifier '{name}' used without declaration.")
            addr = symbol_table[name][0]
            self.match("identifier")
            emit("PUSHM", addr)

        # boolean literal
        elif (self.current_token.token_type == "keyword" and
            self.current_token.lexeme in {"true", "false"}):
            lit = 1 if self.current_token.lexeme == "true" else 0
            self.match("keyword")
            emit("PUSHI", lit)

        else:
            self.error(f"Syntax Error: Expected expression, found {self.current_token}")

        # handle binary operators
        while (self.current_token
            and self.current_token.token_type == "operator"
            and self.current_token.lexeme in {"+", "-", "*", "/"}):
            op = self.current_token.lexeme
            self.match("operator")
            self.expression()
            if op == "+":
                emit("A")
            elif op == "-":
                emit("S")
            elif op == "*":
                emit("M")
            elif op == "/":
                emit("D")

    def term(self):
        pr("<Term> -> <Factor> { (*|/) <Factor> }")
        self.factor()
        while self.current_token and self.current_token.lexeme in {"*", "/"}:
            op = self.current_token.lexeme
            self.match("operator")
            self.factor()
            emit("MUL" if op == "*" else "DIV", comment=f"op {op}")

    def factor(self):
        if (self.current_token and self.current_token.lexeme == "-"):
            pr("<Factor> -> - <Primary>")
            self.match("operator", "-")
            self.primary()
            emit("NEG", comment="unary -")
        else:
            self.primary()

    def primary(self):
        if self.current_token is None:
            self.error("Unexpected end of input in primary")
        if self.current_token.token_type == "identifier":
            # check for function call
            if (self.current_token_index + 1 < len(self.tokens) and 
                self.tokens[self.current_token_index+1].token_type == "separator" and 
                self.tokens[self.current_token_index+1].lexeme == "("):
                self.match("identifier")
                self.match("separator", "(")
                self.ids()
                self.match("separator", ")")
            else:
                self.match("identifier")
        elif self.current_token.token_type == "integer":
            self.match("integer")
        elif self.current_token.token_type == "real":
            self.match("real")
        elif self.current_token.token_type == "keyword" and self.current_token.lexeme in {"true", "false"}:
            self.match("keyword")
        elif self.current_token.token_type == "separator" and self.current_token.lexeme == "(":
            self.match("separator", "(")
            self.expression()
            self.match("separator", ")")
        else:
            self.error("Expected primary expression")

# main(): Processes test files, tokenizes, parses, prints symbol table, assembly & identifiers
def main():
    test_files   = ["test1.rat25s", "test2.rat25s", "test3.rat25s"]
    output_files = ["output1.txt",   "output2.txt",   "output3.txt"]
    global symbol_table, Memory_Address, instructions, instr_ptr

    for i in range(len(test_files)):
        fname    = test_files[i]
        out_fname = output_files[i]

        # capture everything this iteration prints
        buf = io.StringIO()
        with redirect_stdout(buf):
            # reset state for each test
            symbol_table.clear()
            Memory_Address = 10000
            instructions   = [None] * MAX_INSTR
            instr_ptr      = 1

            print(f"\n=== Running Test Case: {fname} ===\n")
            try:
                source_code = open(fname).read()
            except FileNotFoundError:
                print(f"Error: {fname} not found. Skipping...\n")
                continue

            tokens = lexer(source_code)

            # print tokens
            print("Tokens:")
            print("Token         Lexeme")
            print("----------------------")
            for token in tokens:
                print(str(token))
            print()

            # capture parsing output
            buf2 = io.StringIO()
            parser = Parser(tokens)
            with redirect_stdout(buf2):
                parser.parse_rat25s()
            parsing_output = buf2.getvalue()

            # print Parsing
            print("Parsing Output:")
            print(parsing_output)

            # print symbol table
            print_symbol_table()

            # print assembly
            print_assembly()

            print("\n" + "="*40 + "\n")

        # replay to terminal
        print(buf.getvalue(), end="")

        # write to output file
        with open(out_fname, "w") as fout:
            fout.write(buf.getvalue())

if __name__ == "__main__":
    main()
