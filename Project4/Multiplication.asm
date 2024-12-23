


@R0
D=A
@R2
M=D

@R0
D=M
@End
D;JEQ

@R1 
D=M
@End
D;JEQ

@R0
D=M
@R2
M=D

@R1 
D=M
@counter
M=D


(Loop)

@counter
M=M-1
D=M
@End
D;JEQ

@R0
D=M
@R2
M=D+M
@counter
D=M
@Loop
D;JGT


(End)
@End
0;JEQ