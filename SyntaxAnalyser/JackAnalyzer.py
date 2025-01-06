from ast import List
import os
import sys
import xml.etree.ElementTree as ET

class JackParser:
    def __init__(self):
        self.current_token_idx = 0
        self.tokens = []

    def peek(self):
        if self.current_token_idx < len(self.tokens):
            return self.tokens[self.current_token_idx]
        return None

    def advance(self):
        token = self.peek()
        self.current_token_idx += 1
        return token

    def eat(self, expected_token):
        token = self.advance()
        if token != expected_token:
            raise Exception(f"Expected {expected_token}, got {token}")
        return token

    def parse_class(self):
        root = ET.Element("class")

        # class keyword
        keyword = ET.SubElement(root, "keyword")
        keyword.text = f" {self.advance()} "

        # class name
        identifier = ET.SubElement(root, "identifier")
        identifier.text = f" {self.advance()} "

        # opening brace
        symbol = ET.SubElement(root, "symbol")
        symbol.text = " { "
        self.advance()

        # Parse class body
        while self.peek() and self.peek() != "}":
            token = self.peek()
            if token in ["static", "field"]:
                self.parse_class_var_dec(root)
            elif token in ["constructor", "function", "method"]:
                self.parse_subroutine_dec(root)

        # closing brace
        symbol = ET.SubElement(root, "symbol")
        symbol.text = " } "
        self.advance()

        return root

    def parse_class_var_dec(self, parent):
        var_dec = ET.SubElement(parent, "classVarDec")

        # static/field
        keyword = ET.SubElement(var_dec, "keyword")
        keyword.text = f" {self.advance()} "

        # type
        token = self.advance()
        if token in ["int", "char", "boolean"]:
            elem = ET.SubElement(var_dec, "keyword")
        else:
            elem = ET.SubElement(var_dec, "identifier")
        elem.text = f" {token} "

        # First variable name
        identifier = ET.SubElement(var_dec, "identifier")
        identifier.text = f" {self.advance()} "

        # Additional variable names
        while self.peek() == ",":
            symbol = ET.SubElement(var_dec, "symbol")
            symbol.text = " , "
            self.advance()

            identifier = ET.SubElement(var_dec, "identifier")
            identifier.text = f" {self.advance()} "

        # semicolon
        symbol = ET.SubElement(var_dec, "symbol")
        symbol.text = " ; "
        self.advance()

    def parse_subroutine_dec(self, parent):
        sub_dec = ET.SubElement(parent, "subroutineDec")

        # constructor/function/method
        keyword = ET.SubElement(sub_dec, "keyword")
        keyword.text = f" {self.advance()} "

        # return type
        token = self.advance()
        if token in ["void", "int", "char", "boolean"]:
            elem = ET.SubElement(sub_dec, "keyword")
        else:
            elem = ET.SubElement(sub_dec, "identifier")
        elem.text = f" {token} "

        # subroutine name
        identifier = ET.SubElement(sub_dec, "identifier")
        identifier.text = f" {self.advance()} "

        # parameter list
        symbol = ET.SubElement(sub_dec, "symbol")
        symbol.text = " ( "
        self.advance()

        param_list = ET.SubElement(sub_dec, "parameterList")
        self.parse_parameter_list(param_list)

        symbol = ET.SubElement(sub_dec, "symbol")
        symbol.text = " ) "
        self.advance()

        # subroutine body
        self.parse_subroutine_body(sub_dec)

    def parse_subroutine_body(self, parent):
        body = ET.SubElement(parent, "subroutineBody")
        
        # opening brace
        symbol = ET.SubElement(body, "symbol")
        symbol.text = " { "
        self.advance()
        
        # Handle var declarations
        while self.peek() == "var":
            self.parse_var_dec(body)
        
        # statements
        statements = ET.SubElement(body, "statements")
        while self.peek() != "}":
            self.parse_statement(statements)
        
        # closing brace
        symbol = ET.SubElement(body, "symbol")
        symbol.text = " } "
        self.advance()

    def parse_var_dec(self, parent):
        """Parse local variable declarations"""
        var_dec = ET.SubElement(parent, "varDec")
        
        # var keyword
        keyword = ET.SubElement(var_dec, "keyword")
        keyword.text = " var "
        self.advance()
        
        # type
        token = self.advance()
        if token in ["int", "char", "boolean"]:
            elem = ET.SubElement(var_dec, "keyword")
        else:
            elem = ET.SubElement(var_dec, "identifier")
        elem.text = f" {token} "
        
        # First variable name
        identifier = ET.SubElement(var_dec, "identifier")
        identifier.text = f" {self.advance()} "
        
        # Additional variables
        while self.peek() == ",":
            symbol = ET.SubElement(var_dec, "symbol")
            symbol.text = " , "
            self.advance()
            
            identifier = ET.SubElement(var_dec, "identifier")
            identifier.text = f" {self.advance()} "
        
        # semicolon
        symbol = ET.SubElement(var_dec, "symbol")
        symbol.text = " ; "
        self.advance()

    def parse_statement(self, parent):
        token = self.peek()
        if token == "let":
            self.parse_let_statement(parent)
        elif token == "if":
            self.parse_if_statement(parent)
        elif token == "while":
            self.parse_while_statement(parent)
        elif token == "do":
            self.parse_do_statement(parent)
        elif token == "return":
            self.parse_return_statement(parent)

    def parse_let_statement(self, parent):
        let_statement = ET.SubElement(parent, "letStatement")

        # let keyword
        keyword = ET.SubElement(let_statement, "keyword")
        keyword.text = " let "
        self.advance()

        # variable name
        identifier = ET.SubElement(let_statement, "identifier")
        identifier.text = f" {self.advance()} "

        # Optional array indexing
        if self.peek() == "[":
            symbol = ET.SubElement(let_statement, "symbol")
            symbol.text = " [ "
            self.advance()

            self.parse_expression(let_statement)

            symbol = ET.SubElement(let_statement, "symbol")
            symbol.text = " ] "
            self.advance()

        # equals sign
        symbol = ET.SubElement(let_statement, "symbol")
        symbol.text = " = "
        self.advance()

        self.parse_expression(let_statement)

        # semicolon
        symbol = ET.SubElement(let_statement, "symbol")
        symbol.text = " ; "
        self.advance()

    def parse_if_statement(self, parent):
        if_statement = ET.SubElement(parent, "ifStatement")

        # if keyword
        keyword = ET.SubElement(if_statement, "keyword")
        keyword.text = " if "
        self.advance()

        # opening parenthesis
        symbol = ET.SubElement(if_statement, "symbol")
        symbol.text = " ( "
        self.advance()

        self.parse_expression(if_statement)

        # closing parenthesis
        symbol = ET.SubElement(if_statement, "symbol")
        symbol.text = " ) "
        self.advance()

        # opening brace
        symbol = ET.SubElement(if_statement, "symbol")
        symbol.text = " { "
        self.advance()

        # if body statements
        statements = ET.SubElement(if_statement, "statements")
        while self.peek() != "}":
            self.parse_statement(statements)

        # closing brace
        symbol = ET.SubElement(if_statement, "symbol")
        symbol.text = " } "
        self.advance()

        # Optional else clause
        if self.peek() == "else":
            keyword = ET.SubElement(if_statement, "keyword")
            keyword.text = " else "
            self.advance()

            symbol = ET.SubElement(if_statement, "symbol")
            symbol.text = " { "
            self.advance()

            statements = ET.SubElement(if_statement, "statements")
            while self.peek() != "}":
                self.parse_statement(statements)

            symbol = ET.SubElement(if_statement, "symbol")
            symbol.text = " } "
            self.advance()

    def parse_while_statement(self, parent):
        while_statement = ET.SubElement(parent, "whileStatement")

        # while keyword
        keyword = ET.SubElement(while_statement, "keyword")
        keyword.text = " while "
        self.advance()

        # opening parenthesis
        symbol = ET.SubElement(while_statement, "symbol")
        symbol.text = " ( "
        self.advance()

        self.parse_expression(while_statement)

        # closing parenthesis
        symbol = ET.SubElement(while_statement, "symbol")
        symbol.text = " ) "
        self.advance()

        # opening brace
        symbol = ET.SubElement(while_statement, "symbol")
        symbol.text = " { "
        self.advance()

        # statements
        statements = ET.SubElement(while_statement, "statements")
        while self.peek() != "}":
            self.parse_statement(statements)

        # closing brace
        symbol = ET.SubElement(while_statement, "symbol")
        symbol.text = " } "
        self.advance()

    def parse_parameter_list(self, parent):
        if self.peek() and self.peek() != ")":
            # type
            token = self.advance()
            if token in ["int", "char", "boolean"]:
                elem = ET.SubElement(parent, "keyword")
            else:
                elem = ET.SubElement(parent, "identifier")
            elem.text = f" {token} "
            
            # parameter name
            identifier = ET.SubElement(parent, "identifier")
            identifier.text = f" {self.advance()} "
            
            while self.peek() == ",":
                symbol = ET.SubElement(parent, "symbol")
                symbol.text = " , "
                self.advance()
                
                # type
                token = self.advance()
                if token in ["int", "char", "boolean"]:
                    elem = ET.SubElement(parent, "keyword")
                else:
                    elem = ET.SubElement(parent, "identifier")
                elem.text = f" {token} "
                
                # parameter name
                identifier = ET.SubElement(parent, "identifier")
                identifier.text = f" {self.advance()} "
        else:
            # Empty parameter list - create the tag without any content
            parent.text = ""

    def parse_do_statement(self, parent):
        do_statement = ET.SubElement(parent, "doStatement")
        
        # do keyword
        keyword = ET.SubElement(do_statement, "keyword")
        keyword.text = " do "
        self.advance()
        
        # subroutine call
        identifier = ET.SubElement(do_statement, "identifier")
        identifier.text = f" {self.advance()} "
        
        if self.peek() == ".":
            symbol = ET.SubElement(do_statement, "symbol")
            symbol.text = " . "
            self.advance()
            
            identifier = ET.SubElement(do_statement, "identifier")
            identifier.text = f" {self.advance()} "
        
        # opening parenthesis
        symbol = ET.SubElement(do_statement, "symbol")
        symbol.text = " ( "
        self.advance()
        
        # expression list - handle empty case
        expr_list = ET.SubElement(do_statement, "expressionList")
        if self.peek() == ")":
            expr_list.text = ""  # This will make it self-closing
        else:
            self.parse_expression(expr_list)
            while self.peek() == ",":
                symbol = ET.SubElement(expr_list, "symbol")
                symbol.text = " , "
                self.advance()
                self.parse_expression(expr_list)
        
        # closing parenthesis
        symbol = ET.SubElement(do_statement, "symbol")
        symbol.text = " ) "
        self.advance()
        
        # semicolon
        symbol = ET.SubElement(do_statement, "symbol")
        symbol.text = " ; "
        self.advance()

    def parse_return_statement(self, parent):
        return_statement = ET.SubElement(parent, "returnStatement")

        # return keyword
        keyword = ET.SubElement(return_statement, "keyword")
        keyword.text = " return "
        self.advance()

        # Optional expression
        if self.peek() != ";":
            self.parse_expression(return_statement)

        # semicolon
        symbol = ET.SubElement(return_statement, "symbol")
        symbol.text = " ; "
        self.advance()

    def parse_expression(self, parent):
        expression = ET.SubElement(parent, "expression")

        # First term
        self.parse_term(expression)

        # Additional (operator, term) pairs
        while self.peek() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
            symbol = ET.SubElement(expression, "symbol")
            symbol.text = f" {self.advance()} "
            self.parse_term(expression)

    def parse_term(self, parent):
        term = ET.SubElement(parent, "term")
        token = self.peek()

        if token.isdigit():
            int_const = ET.SubElement(term, "integerConstant")
            int_const.text = f" {self.advance()} "
        elif token.startswith('"'):
            str_const = ET.SubElement(term, "stringConstant")
            str_const.text = f" {self.advance()[1:-1]} "  # Remove quotes
        elif token in ["true", "false", "null", "this"]:
            keyword = ET.SubElement(term, "keyword")
            keyword.text = f" {self.advance()} "
        elif token in ["-", "~"]:
            symbol = ET.SubElement(term, "symbol")
            symbol.text = f" {self.advance()} "
            self.parse_term(term)
        elif token == "(":
            symbol = ET.SubElement(term, "symbol")
            symbol.text = " ( "
            self.advance()
            self.parse_expression(term)
            symbol = ET.SubElement(term, "symbol")
            symbol.text = " ) "
            self.advance()
        else:
            # Variable or subroutine call
            identifier = ET.SubElement(term, "identifier")
            identifier.text = f" {self.advance()} "

            if self.peek() == "[":  # Array access
                symbol = ET.SubElement(term, "symbol")
                symbol.text = " [ "
                self.advance()
                self.parse_expression(term)
                symbol = ET.SubElement(term, "symbol")
                symbol.text = " ] "
                self.advance()
            elif self.peek() == "(":  # Subroutine call
                symbol = ET.SubElement(term, "symbol")
                symbol.text = " ( "
                self.advance()
                expr_list = ET.SubElement(term, "expressionList")
                if self.peek() != ")":
                    self.parse_expression(expr_list)
                    while self.peek() == ",":
                        symbol = ET.SubElement(expr_list, "symbol")
                        symbol.text = " , "
                        self.advance()
                        self.parse_expression(expr_list)
                symbol = ET.SubElement(term, "symbol")
                symbol.text = " ) "
                self.advance()
            elif self.peek() == ".":  # Method call
                symbol = ET.SubElement(term, "symbol")
                symbol.text = " . "
                self.advance()
                identifier = ET.SubElement(term, "identifier")
                identifier.text = f" {self.advance()} "
                symbol = ET.SubElement(term, "symbol")
                symbol.text = " ( "
                self.advance()
                expr_list = ET.SubElement(term, "expressionList")
                if self.peek() != ")":
                    self.parse_expression(expr_list)
                    while self.peek() == ",":
                        symbol = ET.SubElement(expr_list, "symbol")
                        symbol.text = " , "
                        self.advance()
                        self.parse_expression(expr_list)
                symbol = ET.SubElement(term, "symbol")
                symbol.text = " ) "
                self.advance()


def tokenize(content):
    """Convert input string into a list of tokens."""
    tokens = []
    current_token = ""
    i = 0
    in_string = False
    in_comment = False

    while i < len(content):
        char = content[i]

        # Handle string literals
        if char == '"':
            if not in_comment:
                if in_string:
                    current_token += char
                    tokens.append(current_token)
                    current_token = ""
                    in_string = False
                else:
                    if current_token:
                        tokens.append(current_token)
                    current_token = char
                    in_string = True
            i += 1
            continue

        # Handle comments
        if char == "/" and i + 1 < len(content):
            if content[i + 1] == "/":  # Single line comment
                i = content.find("\n", i)
                if i == -1:
                    break
                i += 1
                continue
            elif content[i + 1] == "*":  # Multi-line comment
                i = content.find("*/", i)
                if i == -1:
                    break
                i += 2
                continue

        if in_string:
            current_token += char
        elif not in_comment:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif char in "{}()[].,;+-*/&|<>=~":
                if current_token:
                    tokens.append(current_token)
                tokens.append(char)
                current_token = ""
            else:
                current_token += char

        i += 1

    if current_token:
        tokens.append(current_token)

    return [token for token in tokens if token.strip()]


def process_file(file_path):
    """Process a Jack file and generate XML output."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    parser = JackParser()
    parser.tokens = tokenize(content)
    xml_tree = parser.parse_class()

    def indent(elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for subelem in elem:
                indent(subelem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            if elem.tag in ['parameterList', 'expressionList']:
                elem.text = i + "  "

    indent(xml_tree)
    
    # Convert to string with proper formatting
    xml_str = ET.tostring(xml_tree, encoding='unicode')
    # Replace self-closing tags with full tags
    xml_str = xml_str.replace('/>', '></parameterList>' if 'parameterList' in xml_str else '></expressionList>')
    return xml_str

def process_directory(directory_path):
    """Process all .jack files in the directory."""
    processed_files = []
    
    # Get all .jack files in the directory (non-recursive)
    files = [f for f in os.listdir(directory_path) if f.endswith('.jack')]
    
    # Process each .jack file
    for jack_file in files:
        input_path = os.path.join(directory_path, jack_file)
        output_path = input_path.replace('.jack', '.xml')
        
        try:
            xml_output = process_file(input_path)
            with open(output_path, 'w') as f:
                f.write(xml_output)
            processed_files.append((input_path, True, None))
        except Exception as e:
            processed_files.append((input_path, False, str(e)))
    
    return processed_files

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_path>")
        print("input_path can be either a .jack file or a directory containing .jack files")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Check if input path exists
    if not os.path.exists(input_path):
        print(f"Error: Path '{input_path}' does not exist")
        sys.exit(1)
    
    # Process based on whether it's a file or directory
    if os.path.isfile(input_path):
        if not input_path.endswith('.jack'):
            print("Error: Input file must be a .jack file")
            sys.exit(1)
            
        try:
            xml_output = process_file(input_path)
            output_path = input_path.replace('.jack', '.xml')
            with open(output_path, 'w') as f:
                f.write(xml_output)
            print(f"Successfully processed {input_path}")
        except Exception as e:
            print(f"Error processing {input_path}: {str(e)}")
            sys.exit(1)
    
    else:  # Directory
        processed_files = process_directory(input_path)
        
        # Print summary
        print("\nProcessing Summary:")
        print("-" * 50)
        
        success_count = sum(1 for _, success, _ in processed_files if success)
        fail_count = len(processed_files) - success_count
        
        for file_path, success, error in processed_files:
            if success:
                print(f"✓ Successfully processed: {file_path}")
            else:
                print(f"✗ Failed to process: {file_path}")
                print(f"  Error: {error}")
        
        print("-" * 50)
        print(f"Total files processed: {len(processed_files)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {fail_count}")

if __name__ == "__main__":
    main()