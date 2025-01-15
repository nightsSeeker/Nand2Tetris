import re
from typing import List, Optional
from VMEngine import VMEngine
from SymbolTable import SymbolTable

class JackParser:
    def __init__(self):
        self.current_token_idx = 0
        self.tokens: List[str] = []
        self.symbol_table = SymbolTable()
        self.vm_engine = VMEngine()
        self.vm_commands: List[str] = []
        self.current_class = ""
        self.current_subroutine = ""
        self.while_label_counter = 0
        self.if_label_counter = 0

    def peek(self) -> Optional[str]:
        if self.current_token_idx < len(self.tokens):
            return self.tokens[self.current_token_idx]
        return None

    def advance(self) -> Optional[str]:
        token = self.peek()
        self.current_token_idx += 1
        return token

    def parse_class(self):
        """Parse a Jack class"""
        self.advance()  # class
        self.current_class = self.advance()  # className
        self.symbol_table.startClass(self.current_class)
        
        self.advance()  # {

        # Class-level variable declarations
        while self.peek() and self.peek() in ["static", "field"]:
            self.parse_class_var_dec()

        # Subroutine declarations
        while self.peek() and self.peek() in ["constructor", "function", "method"]:
            self.parse_subroutine_dec()

        self.advance()  # }
        
        # Ensure Main class has a main function with proper signature for Sys.init call
        if self.current_class == "Main":
            found_main = False
            for cmd in self.vm_commands:
                if cmd.startswith("function Main.main"):
                    found_main = True
                    break
            if not found_main:
                raise Exception("Main class must contain a main function")
                
        return self.vm_commands

    def parse_class_var_dec(self):
        """Parse class-level variable declarations"""
        kind = self.advance()  # static/field
        type_ = self.advance()  # type
        name = self.advance()  # varName
        
        self.symbol_table.define(name, type_, kind)
        
        while self.peek() == ",":
            self.advance()  # ,
            name = self.advance()  # varName
            self.symbol_table.define(name, type_, kind)
            
        self.advance()  # ;

    def parse_parameter_list(self) -> int:
        """Parse subroutine parameter list and return number of parameters"""
        param_count = 0
        
        # Handle methods by adding 'this' as first parameter implicitly
        if self.peek() != ")":
            # First parameter
            type_ = self.advance()  # type
            name = self.advance()  # paramName
            self.symbol_table.define(name, type_, "argument")
            param_count = 1
            
            # Additional parameters
            while self.peek() == ",":
                self.advance()  # ,
                type_ = self.advance()  # type
                name = self.advance()  # paramName
                self.symbol_table.define(name, type_, "argument")
                param_count += 1
                
        return param_count

    def parse_subroutine_dec(self):
        """Parse subroutine declarations"""
        subroutine_type = self.advance()  # constructor/function/method
        return_type = self.advance()  # return type
        subroutine_name = self.advance()  # subroutineName
        
        full_subroutine_name = f"{self.current_class}.{subroutine_name}"
        self.current_subroutine = subroutine_name
        self.symbol_table.startSubroutine(subroutine_name, subroutine_type)

        # Special handling for Main.main
        if self.current_class == "Main" and subroutine_name == "main":
            if subroutine_type != "function" or return_type != "void":
                raise Exception("Main.main must be declared as 'function void main'")

        self.advance()  # (
        nArgs = self.parse_parameter_list()
        self.advance()  # )
        
        # Subroutine body
        self.advance()  # {
        
        # Count local variables
        nVars = 0
        saved_pos = self.current_token_idx
        while self.peek() == "var":
            nVars += self.count_local_vars()
        self.current_token_idx = saved_pos

        # Write function declaration
        self.vm_commands.append(self.vm_engine.writeFunc(full_subroutine_name, nVars))
        
        # Handle this pointer for methods and constructors
        if subroutine_type == "method":
            self.vm_commands.extend([
                "push argument 0",
                "pop pointer 0"
            ])
        elif subroutine_type == "constructor":
            # Allocate memory for object
            field_count = self.symbol_table.varCount("field")
            self.vm_commands.extend([
                f"push constant {field_count}",
                "call Memory.alloc 1",
                "pop pointer 0"
            ])

        # Parse variable declarations and statements
        while self.peek() == "var":
            self.parse_var_dec()
            
        self.parse_statements(return_type)
        
        self.advance()  # }

    def parse_let_statement(self):
        """Parse let statements"""
        self.advance()  # let
        var_name = self.advance()  # varName
        
        # Handle array assignment
        is_array = False
        if self.peek() == "[":
            is_array = True
            self.advance()  # [
            
            # Push array base address
            segment, index = self.symbol_table.resolveSymbol(var_name)
            self.vm_commands.append(self.vm_engine.writePush(segment, index))
            
            # Push and compute array index
            self.parse_expression()
            self.advance()  # ]
            
            self.vm_commands.append("add")  # Compute target address
            
        self.advance()  # =
        self.parse_expression()  # Expression to assign
        
        if is_array:
            self.vm_commands.extend(self.vm_engine.writeArrayAccess(is_write=True))
        else:
            segment, index = self.symbol_table.resolveSymbol(var_name)
            self.vm_commands.append(self.vm_engine.writePop(segment, index))
            
        self.advance()  # ;

    def parse_if_statement(self):
        """Parse if statements"""
        label_true = f"IF_TRUE{self.if_label_counter}"
        label_false = f"IF_FALSE{self.if_label_counter}"
        label_end = f"IF_END{self.if_label_counter}"
        self.if_label_counter += 1
        
        self.advance()  # if
        self.advance()  # (
        self.parse_expression()
        self.advance()  # )
        
        # if-goto TRUE_LABEL
        self.vm_commands.append(self.vm_engine.writeIfGoTo(label_true))
        self.vm_commands.append(self.vm_engine.writeGoTo(label_false))
        self.vm_commands.append(self.vm_engine.writeLabel(label_true))
        
        self.advance()  # {
        self.parse_statements("")
        self.advance()  # }
        
        # Handle optional else
        if self.peek() == "else":
            self.vm_commands.append(self.vm_engine.writeGoTo(label_end))
            self.vm_commands.append(self.vm_engine.writeLabel(label_false))
            
            self.advance()  # else
            self.advance()  # {
            self.parse_statements("")
            self.advance()  # }
            
            self.vm_commands.append(self.vm_engine.writeLabel(label_end))
        else:
            self.vm_commands.append(self.vm_engine.writeLabel(label_false))

    def parse_while_statement(self):
        """Parse while statements"""
        label_exp = f"WHILE_EXP{self.while_label_counter}"
        label_end = f"WHILE_END{self.while_label_counter}"
        self.while_label_counter += 1
        
        self.advance()  # while
        
        self.vm_commands.append(self.vm_engine.writeLabel(label_exp))
        
        self.advance()  # (
        self.parse_expression()
        self.advance()  # )
        
        self.vm_commands.append("not")  # Negate condition
        self.vm_commands.append(self.vm_engine.writeIfGoTo(label_end))
        
        self.advance()  # {
        self.parse_statements("")
        self.advance()  # }
        
        self.vm_commands.append(self.vm_engine.writeGoTo(label_exp))
        self.vm_commands.append(self.vm_engine.writeLabel(label_end))

    def parse_var_dec(self):
        """Parse local variable declarations"""
        self.advance()  # var
        type_ = self.advance()  # type (int, char, boolean, or class name)
        name = self.advance()  # varName
        
        # Define first variable
        self.symbol_table.define(name, type_, "local")
        
        # Handle additional variables in the same declaration
        while self.peek() == ",":
            self.advance()  # ,
            name = self.advance()  # varName
            self.symbol_table.define(name, type_, "local")
            
        self.advance()  # ;

    def parse_do_statement(self):
        """Parse do statements"""
        self.advance()  # do
        self.parse_subroutine_call()
        self.advance()  # ;
        
        # Void methods must pop the returned value
        self.vm_commands.append("pop temp 0")

    def parse_statements(self, return_type: str):
        """Parse a sequence of statements"""
        while self.peek() and self.peek() in ["let", "if", "while", "do", "return"]:
            token = self.peek()
            if token == "let":
                self.parse_let_statement()
            elif token == "if":
                self.parse_if_statement()
            elif token == "while":
                self.parse_while_statement()
            elif token == "do":
                self.parse_do_statement()
            elif token == "return":
                self.parse_return_statement(return_type)
            
            # If we hit a closing brace or run out of tokens, stop parsing statements
            if not self.peek() or self.peek() == "}":
                break

    def parse_return_statement(self, return_type: str):
        """Parse return statements"""
        self.advance()  # return
        
        if self.peek() != ";":
            self.parse_expression()
        else:
            # Void functions must return 0
            self.vm_commands.append(self.vm_engine.writePush("constant", 0))
            
        self.advance()  # ;
        self.vm_commands.append(self.vm_engine.writeReturn())

    def parse_expression(self):
        """Parse expressions"""
        self.parse_term()
        
        while self.peek() in "+-*/&|<>=":
            op = self.advance()
            self.parse_term()
            self.vm_commands.append(self.vm_engine.writeArithmetic(op))

    def parse_term(self):
        """Parse terms"""
        token = self.peek()
        
        if token.isdigit():  # Integer constant
            self.advance()
            self.vm_commands.append(self.vm_engine.writePush("constant", token))
            
        elif token.startswith('"'):  # String constant
            string = self.advance()[1:-1]  # Remove quotes
            
            # Create string object
            self.vm_commands.append(self.vm_engine.writePush("constant", len(string)))
            self.vm_commands.append("call String.new 1")
            
            # Append each character
            for char in string:
                self.vm_commands.append(self.vm_engine.writePush("constant", ord(char)))
                self.vm_commands.append("call String.appendChar 2")
                
        elif token in ["true", "false", "null", "this"]:  # Keyword constant
            self.advance()
            if token == "true":
                self.vm_commands.extend([
                    "push constant 0",
                    "not"
                ])
            elif token in ["false", "null"]:
                self.vm_commands.append("push constant 0")
            elif token == "this":
                self.vm_commands.append("push pointer 0")
                
        elif token in ["-", "~"]:  # Unary operator
            op = self.advance()
            self.parse_term()
            if op == "-":
                self.vm_commands.append("neg")
            else:
                self.vm_commands.append("not")
                
        elif token == "(":  # Parenthesized expression
            self.advance()  # (
            self.parse_expression()
            self.advance()  # )
            
        else:  # varName or subroutine call
            name = self.advance()
            
            if self.peek() in ["(", "."]:  # Subroutine call
                self.current_token_idx -= 1  # Back up to reparse the name
                self.parse_subroutine_call()
            else:  # Variable
                segment, index = self.symbol_table.resolveSymbol(name)
                self.vm_commands.append(self.vm_engine.writePush(segment, index))
                
                if self.peek() == "[":  # Array access
                    self.advance()  # [
                    self.parse_expression()
                    self.advance()  # ]
                    self.vm_commands.extend(self.vm_engine.writeArrayAccess())

    def parse_subroutine_call(self):
        """Parse subroutine calls"""
        name = self.advance()
        nArgs = 0
        
        if self.peek() == ".":  # Method or function call on object
            self.advance()  # .
            method_name = self.advance()
            
            # Check if it's a method call on an object
            var_type = self.symbol_table.typeOf(name)
            if var_type:  # Method call
                segment, index = self.symbol_table.resolveSymbol(name)
                self.vm_commands.append(self.vm_engine.writePush(segment, index))
                name = f"{var_type}.{method_name}"
                nArgs = 1
            else:  # Function call
                name = f"{name}.{method_name}"
                
        else:  # Method call on this
            self.vm_commands.append("push pointer 0")
            name = f"{self.current_class}.{name}"
            nArgs = 1
            
        self.advance()  # (
        nArgs += self.parse_expression_list()
        self.advance()  # )
        
        self.vm_commands.append(self.vm_engine.writeCall(name, nArgs))

    def parse_term(self):
        """Parse term"""
        token = self.peek()
        
        if token.isdigit():  # Integer constant
            self.vm_commands.append(f"push constant {self.advance()}")
            
        elif token.startswith('"'):  # String constant
            string = self.advance()[1:-1]  # Remove quotes
            self.vm_commands.append(f"push constant {len(string)}")
            self.vm_commands.append("call String.new 1")
            for char in string:
                self.vm_commands.append(f"push constant {ord(char)}")
                self.vm_commands.append("call String.appendChar 2")
                
        elif token in ["true", "false", "null", "this"]:  # Keyword constant
            self.advance()
            if token == "true":
                self.vm_commands.extend([
                    "push constant 0",
                    "not"
                ])
            elif token in ["false", "null"]:
                self.vm_commands.append("push constant 0")
            elif token == "this":
                self.vm_commands.append("push pointer 0")
                
        elif token in ["-", "~"]:  # Unary operator
            op = self.advance()
            self.parse_term()
            if op == "-":
                self.vm_commands.append("neg")
            else:
                self.vm_commands.append("not")
                
        elif token == "(":  # Parenthesized expression
            self.advance()  # (
            self.parse_expression()
            self.advance()  # )
            
        else:  # varName or subroutine call
            next_token = self.tokens[self.current_token_idx + 1] if self.current_token_idx + 1 < len(self.tokens) else None
            
            if next_token in [".", "("]:  # Subroutine call
                self.parse_subroutine_call()
            else:  # Variable
                name = self.advance()
                if self.peek() == "[":  # Array access
                    self.advance()  # [
                    
                    # Push array base
                    segment, index = self.symbol_table.resolveSymbol(name)
                    self.vm_commands.append(f"push {segment} {index}")
                    
                    # Push and compute index
                    self.parse_expression()
                    self.vm_commands.append("add")
                    
                    self.advance()  # ]
                    self.vm_commands.append("pop pointer 1")
                    self.vm_commands.append("push that 0")
                else:  # Simple variable
                    segment, index = self.symbol_table.resolveSymbol(name)
                    self.vm_commands.append(f"push {segment} {index}")

    def parse_expression_list(self) -> int:
        """Parse comma-separated expressions and return number of expressions"""
        nArgs = 0
        
        if self.peek() != ")":
            self.parse_expression()
            nArgs = 1
            
            while self.peek() == ",":
                self.advance()  # ,
                self.parse_expression()
                nArgs += 1
                
        return nArgs

    def count_local_vars(self) -> int:
        """Count local variables in var declaration"""
        count = 1
        self.advance()  # var
        self.advance()  # type
        self.advance()  # varName
        
        while self.peek() == ",":
            self.advance()  # ,
            self.advance()  # varName
            count += 1
            
        self.advance()  # ;
        return count