from ast import List
import os
import sys
from lxml import etree


xml_node_declaration = {
    "static": "classVarDec",
    "field": "classVarDec",
    "constructor": "subroutineDec",
    "function": "subroutineDec",
    "method": "subroutineDec",
    "let": "letStatement",
    "if": "ifStatement",
    "while": "whileStatement",
    "do": "doStatement",
    "return": "returnStatement",
}

keywords = [
    "class",
    "constructor",
    "function",
    "method",
    "field",
    "static",
    "var",
    "int",
    "char",
    "boolean",
    "void",
    "true",
    "false",
    "null",
    "this",
    "let",
    "do",
    "if",
    "else",
    "while",
    "return",
]
symbols = [
    "{",
    "}",
    "(",
    ")",
    "[",
    "]",
    ".",
    ",",
    ";",
    "~",
    "while",
    "return",
]
operands = [
    "+",
    "-",
    "*",
    "/",
    "&",
    "|",
    "<",
    ">",
    "=",
]

def first_occurrence(lst, char1, char2):
   # Get index of first occurrence of each char
   try:
       i1 = lst.index(char1)
       i2 = lst.index(char2)
       return char1 if i1 < i2 else char2
   except ValueError:  # Handle if char not found
       return char2 if char1 not in lst else char1
   
def is_integer(input):
    try:
        int(input)
        return True
    except:
        return False, None


def is_string(input):
    try:
        if input.startswith('"') and input.endswith('"'):
            return True
    except:
        return False


def is_identifier(input):
    if input[0].isnumeric() == False and "".join(input.split("_")).isalnum():
        return True
    return False


def jack_parser(jack_xml, jack_code: List, index=0, stopping_cond=[]):
    if index == len(jack_code):
        return jack_xml

    item = jack_code[index]

    if item in keywords:
        if item in xml_node_declaration.keys():
            value = xml_node_declaration[item]
            jack_xml_chlds = [x for x in jack_xml.iter("statements")]
            if value.endswith("Statement"):
                if "statements" not in [x.tag for x in jack_xml_chlds]:
                    statements = etree.SubElement(jack_xml, "statements")
                    xml_val_block = etree.SubElement(statements, value)
                else:
                    xml_val_block = etree.SubElement(jack_xml_chlds[0], value)
            else:
                xml_val_block = etree.SubElement(jack_xml, value)
            keyword = etree.SubElement(xml_val_block, "keyword")
            keyword.text = item

            index = jack_parser(
                xml_val_block,
                jack_code,
                index + 1,
                (
                    ";"
                    if xml_node_declaration[item]
                    in ["classVarDec", "letStatement", "returnStatement", "doStatement"]
                    else "}"
                ),
            )
            if item in ["if", "while"]:
                item = jack_code[index + 1]
            else:
                item = jack_code[index]
        elif jack_xml.tag == "expressionList" and item != ")":
            expression = etree.SubElement(jack_xml, "expression")
            x =  first_occurrence(jack_code[index:],",",")")
            index = jack_parser(
                expression,
                jack_code,
                index,
                first_occurrence(jack_code[index:],",",")"),
            )
            item = jack_code[index]
        elif jack_xml.tag == "expression":
            term = etree.SubElement(jack_xml, "term")
            keyword = etree.SubElement(term, "keyword")
            keyword.text = item
        else:
            keyword = etree.SubElement(jack_xml, "keyword")
            keyword.text = item
    elif item in symbols + operands:
        if item == "(" and jack_xml.tag == "subroutineDec":
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            jack_xml.append(symbol)
            parameterList = etree.SubElement(jack_xml, "parameterList")
            jack_xml.append(parameterList)
            index = jack_parser(parameterList, jack_code, index + 1, ")")
            item = jack_code[index]
        elif item == "{" and jack_xml.tag in ["subroutineDec"]:
            subroutineBody = etree.SubElement(jack_xml, "subroutineBody")
            symbol = etree.SubElement(subroutineBody, "symbol")
            symbol.text = item
            index = jack_parser(subroutineBody, jack_code, index + 1, "}")
            item = jack_code[index]
        elif item in ["[", "("] and jack_xml.tag in ["ifStatement", "whileStatement"]:
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            expression = etree.SubElement(jack_xml, "expression")
            index = jack_parser(expression, jack_code, index + 1, ")")
            item = jack_code[index]
        elif item in ["[", "("] and jack_xml.tag == "expression":
            term = etree.SubElement(jack_xml, "term")
            symbol = etree.SubElement(term, "symbol")
            expression = etree.SubElement(term, "expression")
            symbol.text = item
            index = jack_parser(expression, jack_code, index + 1, ")")
            symbol = etree.SubElement(term, "symbol")
            symbol.text = ")"
            item = jack_code[index + 1]
        elif item in ["("] and jack_xml.tag.endswith("Statement"):
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            expressionList = etree.SubElement(jack_xml, "expressionList")
            index = jack_parser(expressionList, jack_code, index + 1, ")")
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = ")"
            item = jack_code[index]
        elif jack_xml.tag == "expression" and item in operands:
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
        elif jack_xml.tag == "expressionList" and item in operands:
            expression = etree.SubElement(jack_xml, "expression")
            index = jack_parser(
                expression,
                jack_code,
                index,
                first_occurrence(jack_code[index:],",",")"),
            )
            item = jack_code[index]
        elif jack_xml.tag not in ["expression", "term"]:
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
    elif is_identifier(item):
        if jack_xml.tag == "expression":
            term = etree.SubElement(jack_xml, "term")
            identifier = etree.SubElement(term, "identifier")
            identifier.text = item
        elif jack_xml.tag == "expressionList" and item != ")":
            expression = etree.SubElement(jack_xml, "expression")
            x =  first_occurrence(jack_code[index:],',',')')
            index = jack_parser(
                expression,
                jack_code,
                index,
                first_occurrence(jack_code[index:],',',')'),
            )
            item = jack_code[index]
        elif jack_xml.tag == "letStatement" and jack_code[index - 1] == "=":
            expression = etree.SubElement(jack_xml, "expression")
            index = jack_parser(expression, jack_code, index, ";")
            item = jack_code[index]
        else:
            identifier = etree.SubElement(jack_xml, "identifier")
            identifier.text = item
    elif is_integer(item):
        if jack_xml.tag == "expression":
            term = etree.SubElement(jack_xml, "term")
            integer = etree.SubElement(jack_xml, "integerConstant")
            integer.text = item
            term.append(integer)
        else:
            integer = etree.SubElement(jack_xml, "integerConstant")
            integer.text = item
            jack_xml.append(integer)
    elif is_string(item):
        string = etree.SubElement(jack_xml, "stringConstant")
        string.text = item
        jack_xml.append(string[1])
    if item in stopping_cond and jack_xml.tag in [
        "classVarDec",
        "subroutineDec",
        "parameterList",
        "subroutineBody",
        "letStatement",
        "ifStatement",
        "whileStatement",
        "doStatement",
        "returnStatement",
        "term",
        "expression",
        "expressionList",
    ]:
        return index
    return jack_parser(jack_xml, jack_code, index + 1, stopping_cond)


def tokenise(file_name: str) -> List:
    # Read and process the file
    with open(file_name, "r") as file:
        # Filter out comments and empty lines, split by spaces
        lines = [
            line.partition("//")[0]  # Remove inline comments
            for line in file.readlines()
            if line.strip()
            and not line.strip().startswith(("//", "/**"))  # Skip full-line comments
        ]

        # Split lines into words and flatten the list
        words = [word for line in lines for word in line.split()]

        # Process each word into tokens
        jack_code = []
        for word in words:
            if not word:  # Skip empty strings
                continue

            # Handle newline characters
            word = word.split("\n")[0]

            # Build tokens character by character
            current_token = ""
            for char in word:
                if char.isalnum():
                    current_token += char
                else:
                    # Add accumulated alphanumeric token if it exists
                    if current_token:
                        jack_code.append(current_token)
                        current_token = ""
                    # Add the special character as a separate token
                    jack_code.append(char)

            # Add any remaining token
            if current_token:
                jack_code.append(current_token)
        return jack_code


if __name__ == "__main__":
    file_name = sys.argv[1]
    jack_xml = etree.Element("class")
    jack_code = tokenise(file_name)
    jack_xml = etree.tostring(
        jack_parser(jack_xml, jack_code), pretty_print=True
    ).decode()
    output_file = file_name.rstrip(".jack") + ".xml"
    # output_file = os.path.join(file_name, os.path.basename(file_name) + ".xml")
    with open(output_file, "w") as file:
        file.write(jack_xml)
