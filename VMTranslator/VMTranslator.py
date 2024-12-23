import os
import sys
import types

jmp_tracker = -1
def inc():
     global jmp_tracker
     jmp_tracker+=1
     return jmp_tracker

def get_comparison_command(op_str):
    i = inc()
    unique_for_each = {'eq':'D;JEQ','gt':'D;JGT','lt':'D;JLT'}
    return ['D=M-D', 'M=-1',f'@end{i}', unique_for_each[op_str],'@SP','A=M-1','M=0',f'(end{i})']

arithmetic_commands = {'add':['M=D+M'], 'sub':['M=M-D'],'and':['M=D&M'],'or':['M=D|M'],
                       'eq':get_comparison_command,'gt':get_comparison_command,'lt':get_comparison_command,
                       'not':'undefined','neg':'undefined'}

def memory_segment(segment):
    if segment == 'local':
        return '@LCL'
    elif segment == 'argument':
        return '@ARG'
    elif segment == 'that':
        return '@THAT'
    elif segment == 'this':
        return '@THIS'
    else:
        return segment
    
def translate_arithmetic_vm_to_assembly(op_str):
    if op_str == "not":
        
        ass = ['@SP', 'A=M-1', 'M=!M']
    elif op_str == "neg":
        
        ass = ['@SP', 'A=M-1', 'M=-M'] 
    else:   
        ass = ['@SP', 'AM=M-1', 'D=M','A=A-1']
        if isinstance(arithmetic_commands[op_str], types.FunctionType):
            
            ass.extend(arithmetic_commands[op_str](op_str))
        else:     
            ass.extend(arithmetic_commands[op_str])
    return ass
         

def translate_push_segment_to_assembly(seg,value):
    if seg == "temp":
        return [f'@{int(value)+5}','D=M', '@SP', 'AM=M+1', 'A=A-1', 'M=D']
    elif seg == "static":
        
        return [f'@{int(value)+16}','D=M', '@SP', 'AM=M+1', 'A=A-1', 'M=D']   
    elif seg == "pointer":
        
        if(value == "0"):
         return ['@THIS', 'D=M','@SP', 'AM=M+1', 'A=A-1','M=D']  
        elif(value == "1"):
           return ['@THAT', 'D=M','@SP', 'AM=M+1', 'A=A-1','M=D']  
    else:
        return [f'{seg}','D=M',f'@{value}', 'A=D+A', 'D=M','@SP','AM=M+1','A=A-1','M=D']

def translate_pop_segment_to_assembly(seg, value):
    if seg == "temp":
        return ['@SP','AM=M-1','D=M',f'@{int(value)+5}','M=D']
    elif seg == "static":
        
        return ['@SP','AM=M-1','D=M',f'@{int(value)+16}','M=D']  
    elif seg == "pointer":
        
        if(value == "0"):
         return ['@SP', 'AM=M-1', 'D=M', '@THIS', 'M=D']  
        elif(value == "1"):
          return ['@SP', 'AM=M-1', 'D=M', '@THAT', 'M=D']  
    else:
        return [f'{seg}','D=M', f'@{value}', 'D=D+A','@R13','M=D', '@SP','AM=M-1','D=M','@R13','A=M','M=D']

def execute_call_procedure(functionName, nargs):
    i = inc()
    pushReturnAddress = [f'@return{i}','D=A','@SP','AM=M+1','A=A-1','M=D']
    pushLCL  = ['@LCL','D=M','@SP','AM=M+1','A=A-1','M=D']
    pushARG  = ['@ARG','D=M','@SP','AM=M+1','A=A-1','M=D']
    pushTHIS  = ['@THIS','D=M','@SP','AM=M+1','A=A-1','M=D']
    pushTHAT  = ['@THAT','D=M','@SP','AM=M+1','A=A-1','M=D']
    repositionARG = ['@5','D=A','@SP','D=M-D',f'@{nargs}','D=D-A','@ARG','M=D']
    repositionLCL = ['@SP','D=M','@LCL','M=D']
    goToFunction = [f'@{functionName}','0;JMP']
    returnAddress = [f'(return{i})']
    return pushReturnAddress+pushLCL+pushARG+pushTHIS+pushTHAT+repositionARG+repositionLCL+goToFunction+returnAddress;

def execute_return_procedure():

    endFrame = ['@LCL','D=M', '@R13', 'M=D']
    retAddr = ['@R13','D=M','@5','A=D-A','D=M','@R14','M=D']
    retValue = ['@SP','A=M-1','D=M','@ARG','A=M','M=D']
    repositionSP = [ '@ARG','D=M+1','@SP','M=D']
    restoreThat = ['@R13','D=M','@1','A=D-A','D=M','@THAT', 'M=D']
    restoreThis = ['@R13','D=M','@2','A=D-A','D=M','@THIS','M=D']
    restoreARG = ['@R13','D=M','@3','A=D-A','D=M','@ARG','M=D']
    restoreLCL = ['@R13','D=M','@4','A=D-A','D=M','@LCL','M=D']
    JumpToReturnAddress = ['@R14','A=M', '0;JMP']
    return endFrame+retAddr+retValue+repositionSP+restoreThat+restoreThis+restoreARG+restoreLCL+JumpToReturnAddress;

def run_bootstrap_code():

    initSP = ['@256','D=A','@SP','M=D']
    initSegments = [
        '@LCL', 'M=0',
        '@ARG', 'M=0',
        '@THIS', 'M=0',
        '@THAT', 'M=0'
    ]
    sysInit =  execute_call_procedure('Sys.init', '0')
    return initSP+initSegments+sysInit;

def process_vm_file(file_name):
    # Check if the file has a .vm extension
    if not file_name.endswith('.vm'):
        print("Error: The file must have a .vm extension.")
        sys.exit(1)

    # Read and clean the contents of the file
    with open(file_name, 'r') as file:
        vm_code = [line.split("//")[0].strip() for line in file.readlines() if line.strip() and not line.strip().startswith("//")]
       
    return vm_code 

def process_directory(dir_path):
    """Process all .vm files in the directory and merge their code."""
    vm_files = [f for f in os.listdir(dir_path) if f.endswith('.vm')]
    if not vm_files:
        print(f"Error: No .vm files found in directory {dir_path}")
        sys.exit(1)
    
    # Start with Sys.vm if it exists, as it contains the bootstrap code
    if 'Sys.vm' in vm_files:
        vm_files.remove('Sys.vm')
        vm_files = ['Sys.vm'] + sorted(vm_files)
    
    merged_vm_code = []
    for vm_file in vm_files:
        file_path = os.path.join(dir_path, vm_file)
        with open(file_path, 'r') as file:
            # Add a comment to mark the start of each file's code
            merged_vm_code.append(f"// Start of {vm_file}")
            vm_code = [line.split("//")[0].strip() for line in file.readlines() 
                      if line.strip() and not line.strip().startswith("//")]
            merged_vm_code.extend(vm_code)
    
    return merged_vm_code

def translate_vm_to_assembly(vm_code, include_bootstrap=False):
    """Modified to optionally include bootstrap code."""
    assembly_code = run_bootstrap_code() if include_bootstrap else []
    for command in vm_code:
        if command.startswith("//"):  # Skip comments
            continue
        # Rest of your existing translation code...
        if command in list(arithmetic_commands.keys()):
            assembly_code.extend(translate_arithmetic_vm_to_assembly(command))
        elif command == "return":
            assembly_code.extend(execute_return_procedure())    
        elif command.startswith("call"):
            assembly_code.extend(execute_call_procedure(command.split(" ")[1],command.split(" ")[2]))                   
        elif command.split(" ")[1] == "constant":
            assembly_code.extend([f'@{command.split(" ")[2]}', 'D=A','@SP','AM=M+1','A=A-1','M=D'])
        elif command.split(" ")[0] == "push":
            assembly_code.extend(translate_push_segment_to_assembly(memory_segment(command.split(" ")[1]),command.split(" ")[2]))    
        elif command.split(" ")[0] == "pop":
            assembly_code.extend(translate_pop_segment_to_assembly(memory_segment(command.split(" ")[1]),command.split(" ")[2])) 
        elif command.split(" ")[0] == "label":
            assembly_code.extend(["("+ command.split(" ")[1]+")"])    
        elif command.split(" ")[0] == "function":
            functionName = command.split(" ")[1]
            nVars = int(command.split(" ")[2])
            assembly_code.extend([f"({functionName})"])
            for _ in range(nVars):
                assembly_code.extend(['@SP', 'AM=M+1', 'A=A-1', 'M=0'])             
        elif command.split(" ")[0] == "if-goto":
            i = inc()
            assembly_code.extend(["@SP", "AM=M-1", "D=M", f'@end{i}',"D;JEQ", "@"+command.split(" ")[1],"0;JMP", f'(end{i})'])              
        elif command.split(" ")[0] == "goto":
            assembly_code.extend(["@"+command.split(" ")[1],"0;JMP"])     
        else:
            assembly_code.append(command)    
    return assembly_code

def main():
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <vm_file_or_directory>")
        sys.exit(1)

    path = sys.argv[1]
    
    # Determine if the path is a file or directory
    if os.path.isfile(path):
        # Single file mode - no bootstrap
        if not path.endswith('.vm'):
            print("Error: The file must have a .vm extension.")
            sys.exit(1)
            
        vm_code = process_vm_file(path)
        asm_code = translate_vm_to_assembly(vm_code, include_bootstrap=False)
        output_file = path.rstrip('.vm') + '.asm'
        
    elif os.path.isdir(path):
        # Directory mode - include bootstrap
        vm_code = process_directory(path)
        asm_code = translate_vm_to_assembly(vm_code, include_bootstrap=True)
        output_file = os.path.join(path, os.path.basename(path) + '.asm')
        
    else:
        print(f"Error: Path {path} does not exist")
        sys.exit(1)
    
    # Write the assembly code to file
    with open(output_file, 'w') as file:
        file.writelines([line + '\n' for line in asm_code])
        
    print(f"Successfully created {output_file}")

if __name__ == "__main__":
    main()