from ast import List
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
    "+",
    "-",
    "*",
    "/",
    "&",
    "|",
    "<",
    ">",
    "=",
    "~",
    "while",
    "return",
]


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
            xml_val_block = etree.SubElement(jack_xml, value)
            keyword = etree.SubElement(jack_xml, "keyword")
            keyword.text = item
            xml_val_block.append(keyword)
            if value.endswith("Statement"):
                statements = etree.SubElement(jack_xml, "statements")
                statements.append(xml_val_block)
                jack_xml.append(statements)
            else:
                jack_xml.append(xml_val_block)
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
            item = jack_code[index]
        else:
            keyword = etree.SubElement(jack_xml, "keyword")
            keyword.text = item
            jack_xml.append(keyword)
    elif item in symbols:
        if item == "(" and jack_xml.tag == "subroutineDec":
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            jack_xml.append(symbol)
            parameterList = etree.SubElement(jack_xml, "parameterList")
            jack_xml.append(parameterList)
            index = jack_parser(parameterList, jack_code, index + 1, ")")
            item = jack_code[index]
        elif item == "{" and jack_xml.tag == "subroutineDec":
            subroutineBody = etree.SubElement(jack_xml, "subroutineBody")
            jack_xml.append(subroutineBody)
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            subroutineBody.append(symbol)
            index = jack_parser(subroutineBody, jack_code, index + 1, "}")
            item = jack_code[index]
        elif jack_code[index - 1] in ["if", "("] and jack_xml.tag in [
            "ifStatement",
            "whileStatement",
        ]:
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            jack_xml.append(symbol)

            expression = etree.SubElement(jack_xml, "expression")
            term = etree.SubElement(jack_xml, "term")
            jack_xml.append(expression)
            expression.append(term)

            index = jack_parser(expression, jack_code, index + 1, ")")
            item = jack_code[index]

        elif jack_xml.tag == "expression":
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            jack_xml.append(symbol)
        else:
            symbol = etree.SubElement(jack_xml, "symbol")
            symbol.text = item
            jack_xml.append(symbol)
    elif is_identifier(item):
        if jack_code[index - 1] == "(" and jack_xml.tag in [
            "ifStatement",
            "whileStatement",
        ]:
            expression = etree.SubElement(jack_xml, "expression")
            term = etree.SubElement(jack_xml, "term")
            jack_xml.append(expression)
            expression.append(term)

            identifier = etree.SubElement(jack_xml, "identifier")
            identifier.text = item
            term.append(identifier)
            index = jack_parser(expression, jack_code, index + 1, ")")
            item = jack_code[index]
        elif jack_xml.tag == "expression":
            term = etree.SubElement(jack_xml, "term")
            identifier = etree.SubElement(jack_xml, "identifier")
            identifier.text = item
            term.append(identifier)
            jack_xml.append(term)
        else:
            identifier = etree.SubElement(jack_xml, "identifier")
            identifier.text = item
            jack_xml.append(identifier)
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
    if item == stopping_cond and jack_xml.tag in [
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
    jack_xml = jack_parser(jack_xml, jack_code)
    print(etree.tostring(jack_xml, pretty_print=True).decode())
