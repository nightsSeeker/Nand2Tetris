from ast import List
import sys


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

    jack_code = tokenise(file_name)
    print(jack_code)
