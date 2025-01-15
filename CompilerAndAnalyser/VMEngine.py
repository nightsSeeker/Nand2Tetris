import string

class VMEngine:
    def __init__(self):
        self.label_counter = 0
        
    def _get_unique_label(self, prefix="LABEL"):
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def writePush(self, segment: string, index: int):
        if segment == "constant":
            return f"push constant {index}"
        elif segment in ["local", "argument", "this", "that", "temp", "pointer", "static"]:
            return f"push {segment} {index}"
        else:
            raise ValueError(f"Invalid segment: {segment}")

    def writePop(self, segment: string, index: int):
        if segment in ["local", "argument", "this", "that", "temp", "pointer", "static"]:
            return f"pop {segment} {index}"
        else:
            raise ValueError(f"Invalid segment: {segment}")
    
    def writeArithmetic(self, arithOp: string):
        arithmetic_ops = {
            "+": "add",
            "-": "sub",
            "*": "call Math.multiply 2",
            "/": "call Math.divide 2",
            "&": "and",
            "|": "or",
            "<": "lt",
            ">": "gt",
            "=": "eq",
            "~": "not",
            "neg": "neg"
        }
        
        if arithOp in arithmetic_ops:
            return arithmetic_ops[arithOp]
        else:
            raise ValueError(f"Invalid arithmetic operation: {arithOp}")
    
    def writeLabel(self, label: string):
        return f"label {label}"
    
    def writeGoTo(self, label: string):
        return f"goto {label}"
    
    def writeIfGoTo(self, label: string):
        return f"if-goto {label}"   
    
    def writeCall(self, name: string, num_args: int):
        return f"call {name} {num_args}"   
    
    def writeFunc(self, name: string, num_locals: int):
        return f"function {name} {num_locals}"

    def writeReturn(self):
        return "return"
        
    def writeComparisonOp(self, op: string):
        true_label = self._get_unique_label("TRUE")
        end_label = self._get_unique_label("END")
        
        return [
            "sub",
            f"if-goto {true_label}",
            "push constant 0",
            f"goto {end_label}",
            f"label {true_label}",
            "push constant -1",
            f"label {end_label}"
        ]
        
    def writeArrayAccess(self, is_write=False):
        """Handle array access operations"""
        if is_write:
            return [
                "pop temp 0",  # Store value to write
                "pop pointer 1",  # Set THAT
                "push temp 0",
                "pop that 0"   # Store value at array index
            ]
        else:
            return [
                "pop pointer 1",  # Set THAT
                "push that 0"    # Get value at array index
            ]