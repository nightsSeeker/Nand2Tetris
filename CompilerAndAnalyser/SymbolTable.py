import string
from typing import Dict, Optional, Tuple

class SymbolTable:
    def __init__(self):
        self.class_symbols: Dict = {}
        self.subroutine_symbols: Dict = {}
        self.index_counters = {
            "static": 0,
            "field": 0,
            "argument": 0,
            "local": 0
        }
        self.current_class = ""
        self.current_subroutine = ""
        
    def startClass(self, class_name: str):
        """Start a new class scope"""
        self.current_class = class_name
        self.class_symbols = {}
        self.index_counters["static"] = 0
        self.index_counters["field"] = 0
        
    def startSubroutine(self, subroutine_name: str, subroutine_type: str):
        """Start a new subroutine scope"""
        self.current_subroutine = subroutine_name
        self.subroutine_symbols = {}
        self.index_counters["argument"] = 0
        self.index_counters["local"] = 0
        
        # If it's a method, add 'this' as first argument
        if subroutine_type == "method":
            self.defineArgument("this", self.current_class)

    def define(self, name: str, type_: str, kind: str) -> None:
        """Define a new identifier"""
        if kind in ["static", "field"]:
            self.class_symbols[name] = {
                "type": type_,
                "kind": kind,
                "index": self.index_counters[kind]
            }
            self.index_counters[kind] += 1
        elif kind in ["argument", "local"]:
            self.subroutine_symbols[name] = {
                "type": type_,
                "kind": kind,
                "index": self.index_counters[kind]
            }
            self.index_counters[kind] += 1

    def defineArgument(self, name: str, type_: str):
        """Helper method to define an argument"""
        self.define(name, type_, "argument")

    def defineLocal(self, name: str, type_: str):
        """Helper method to define a local variable"""
        self.define(name, type_, "local")
        
    def varCount(self, kind: str) -> int:
        """Get number of variables of a given kind"""
        return self.index_counters[kind]

    def kindOf(self, name: str) -> Optional[str]:
        """Get kind of named identifier"""
        if name in self.subroutine_symbols:
            return self.subroutine_symbols[name]["kind"]
        elif name in self.class_symbols:
            return self.class_symbols[name]["kind"]
        return None

    def typeOf(self, name: str) -> Optional[str]:
        """Get type of named identifier"""
        if name in self.subroutine_symbols:
            return self.subroutine_symbols[name]["type"]
        elif name in self.class_symbols:
            return self.class_symbols[name]["type"]
        return None

    def indexOf(self, name: str) -> Optional[int]:
        """Get index of named identifier"""
        if name in self.subroutine_symbols:
            return self.subroutine_symbols[name]["index"]
        elif name in self.class_symbols:
            return self.class_symbols[name]["index"]
        return None
        
    def resolveSymbol(self, name: str) -> Tuple[Optional[str], Optional[int]]:
        """Resolve a symbol to its VM segment and index"""
        kind = self.kindOf(name)
        index = self.indexOf(name)
        
        if kind == "field":
            return "this", index
        elif kind in ["static", "local", "argument"]:
            return kind, index
        return None, None