from ast import List
import os
import sys
import xml.etree.ElementTree as ET

from JackParser import JackParser

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
    """Process a Jack file and generate VM output."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    parser = JackParser()
    parser.tokens = tokenize(content)
    vm_commands = parser.parse_class()
    
    # Join the commands with newlines to create a single string
    return '\n'.join(vm_commands)

def process_directory(directory_path):
    """Process all .jack files in the directory."""
    processed_files = []
    
    # Get all .jack files in the directory (non-recursive)
    files = [f for f in os.listdir(directory_path) if f.endswith('.jack')]
    
    # Make sure to process Main.jack first if it exists
    if 'Main.jack' in files:
        files.remove('Main.jack')
        files.insert(0, 'Main.jack')
    
    # Process each .jack file
    for jack_file in files:
        input_path = os.path.join(directory_path, jack_file)
        try:
            vm_output = process_file(input_path)
            output_path = input_path.replace('.jack', '.vm')
            with open(output_path, 'w') as f:
                f.write(vm_output)
            processed_files.append((input_path, True, None))
        except Exception as e:
            processed_files.append((input_path, False, str(e)))
    
    return processed_files


def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <input_path>")
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
            vm_output = process_file(input_path)
            output_path = input_path.replace('.jack', '.vm')
            with open(output_path, 'w') as f:
                f.write(vm_output)
            print(f"Successfully processed {input_path}")
        except Exception as e:
            print(f"Error processing {input_path}: {str(e)}")
            sys.exit(1)
    else:
        # Process directory
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