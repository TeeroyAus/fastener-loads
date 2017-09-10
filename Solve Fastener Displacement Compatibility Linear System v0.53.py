#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Troy
#
# Created:     31/10/2015
# Copyright:   (c) Troy 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    import numpy as np
##    a = np.array([[1,1,0],[0,10,1],[0,1,1]])
##    b=np.array([1,2,3])
##    c = np.linalg.solve(a,b)
##    print c

    from string import split,join
    import sys
    # Select and Open Input File
    # Use Tkinter to create filedialog GUI
    import Tkinter as tk
    from tkFileDialog import askopenfilename
    root = tk.Tk()
    root.withdraw()
    filename = askopenfilename(filetypes=[('JDAT', '*.jdat')])

    #Open the input file.
    f = file(filename) # if no mode is specified, 'r'ead mode is assumed by default
    while True:
        line = f.readline()
        if len(line) == 0: # Zero length indicates EOF
            break
        line = line.strip()
        if len(line)==0:
            continue
# prepare to capture keywords beginning with *
        if line[0]=="*":
            keyword = line[1:].strip()
            if keyword=="MATERIAL":
                material = True
                fastener = False
                joint = False
            if keyword=="FASTENER":
                material = False
                fastener = True
                joint = False
            if keyword=="JOINT":
                material = False
                fastener = False
                joint = True
            if keyword=="VERBOSE":
                verbose = True
            else:
                verbose = False
# ignore all lines marked as a comment
        elif line[0]=="#":
            continue
# extract relevant information associated with keywords
# In MATERIAL Group expected data are: Es, Ed
        if material and line[0]!="*":
            Temp = split(line,":")
            if Temp[0] =="Es":
                Es = float(Temp[1])
##                print "%s = %.2f" % (Temp[0],Es)
            if Temp[0] =="Ed":
                Ed = float(Temp[1])
##                print "%s = %.2f" % (Temp[0],Ed)
            if Temp[0] =="Ef":
                Ef = float(Temp[1])
##                print "%s = %.2f" % (Temp[0],Ef)

# In FASTENER Group expected data are: NFast, Fast(n)
        if fastener and line[0]!="*":
            Temp = split(line,":")
#            print Temp[0], len(Temp), Temp[1]
            if Temp[0] =="NFast":
                no_of_fasteners = int(Temp[1])
##                print "No. of fasteners = %d" % (no_of_fasteners)

# Set up 0 matrices for all the lists required to hold the segment specific data
                DFast= [0 for _ in range(no_of_fasteners)]
                FastType= [0 for _ in range(no_of_fasteners)]
                Length= [0 for _ in range(no_of_fasteners)]
                Ts_avg= [0 for _ in range(no_of_fasteners)]
                Td_avg= [0 for _ in range(no_of_fasteners)]
                Width= [0 for _ in range(no_of_fasteners)]
                As=[0 for _ in range(no_of_fasteners)]
                Ad=[0 for _ in range(no_of_fasteners)]
                Afast=[0 for _ in range(no_of_fasteners)]
                Bfast=[0 for _ in range(no_of_fasteners)]

            if Temp[0][:4]=="Fast":
                n=int(Temp[0][4:])
                Temp = split(Temp[1],",")
                DFast[n] =float(Temp[0])
                FastType[n] =Temp[1]

# In JOINT Group expected data are: Seg(n).
        if joint and line[0]!="*":
            Temp = split(line,":")
            if Temp[0][:3]=="Seg":
                n=int(Temp[0][3:])
##                print n
                Temp = split(Temp[1],",")
##                print Temp
                Length[n]= float(Temp[0])
                Ts_avg[n]=float(Temp[1])
                Td_avg[n]=float(Temp[2])
                Width[n]=float(Temp[3])
                As[n]=Ts_avg[n]*Width[n]
                if len(Temp)==5:
                    Ad[n]=float(Temp[4])
                else:
                    Ad[n]=Td_avg[n]*Width[n]
            if Temp[0]=="P":
                P=float(Temp[1])

    f.close() # close the file

# Create Compliance Matrices.
    Cs = plate_compliance(Length,Es,As,no_of_fasteners)
    Cd = plate_compliance(Length,Ed,Ad,no_of_fasteners)
    Cf =fastener_compliance(DFast,Ef,Es, Ed, Ts_avg,Td_avg,no_of_fasteners,FastType)

# If verbose state is requested print intermediate matrices
    if verbose:
        print "This is a system of %s equations." %(no_of_fasteners)
        print
        print "The compliance matrix resolves to:"
        print
        print_compliance_matrix(no_of_fasteners)
        print
        print "The component stiffness matrices are:"
        print
        print "Cs=", Cs
        print "Cd=", Cd
        print "Cf=", Cf
        print
    CMatrix=compliance_matrix(no_of_fasteners, Cs, Cd, Cf)
# Solve Linear System Equation of the type
# a X = b
    a=np.array(CMatrix)
    b=P*np.array(Cs)
    fastener_loads = np.linalg.solve(a,b)
    print "Fastener loads:" 
    print
    print "F0...Fn=", fastener_loads
##    sys.exit()


def plate_compliance(L,E,A, no):
    C=[0 for _ in range(no)]
    for x in range(no):
        C[x]=L[x]/(E*A[x])
    return C

def fastener_compliance(Dfast,Ef,Es, Ed, Ts,Td,no_of_fasteners,FastType):
    Cf =[0 for _ in range(no_of_fasteners)]
    for x in range(no_of_fasteners):
        Afast = Acoeff(FastType[x])
        Bfast = Bcoeff(FastType[x])
        Cf[x]=Afast/(Ef*Dfast[x])+Bfast*(1/(Ef*Td[x])+1/(Ef*Ts[x]))
    return Cf

def Acoeff(fast_type):
    if fast_type=="1":
        # Al
        A = 5.0
    elif fast_type=="2":
        # Steel
        A =1.667
    elif fast_type=="3":
        # Titanium
        A = 3.125
    return A

def Bcoeff(fast_type):
    if fast_type=="1":
        # Al
        B = 0.8
    elif fast_type=="2":
        # Steel
        B = 0.86
    elif fast_type=="3":
        # Titanium
        B = 0.82
    return B


def compliance_matrix(no_of_equations, Cs, Cd, Cf):
# Set up a 2D matrix of zeroes to create the template for the Compliance Matrix.
    A = [[0 for _ in range(no_of_equations)] for _ in range(no_of_equations)]
# Build the compliance matrix from the general equation
# m = rows, n= columns

    for m in range(no_of_equations):
        for n in range(no_of_equations):
            if m>n:
                A[m][n]=Cs[m]+ Cd[m]
            elif m==n:
                A[m][n]=Cs[m]+ Cd[m]+ Cf[m]
            elif n==m+1:
                A[m][m+1]=-Cf[m+1]
    return A


def print_compliance_matrix(no_of_equations):
# Set up a 2D matrix of zeroes to create the template for the Compliance Matrix.
    A = [['0' for _ in range(no_of_equations)] for _ in range(no_of_equations)]
# printing the equation as text can help check that the variables are correct
# and the general equation is working

# work out max no. of characters
# 12 + length of m
# m = rows, n= columns
    
    no_characters = 12 + len(str(no_of_equations))
    max_length=0
    for m in range(no_of_equations):            
        for n in range(no_of_equations):
            if m>n:
                A[m][n]="(Cs"+str(m)+" + Cd"+str(m)+")"
                #A[m][n]= A[m][n].rjust(no_characters)
            elif m==n:
                A[m][n]="(Cs"+str(m)+" + Cd"+str(m)+" + Cf"+str(m)+")"
                #A[m][n]= A[m][n].rjust(no_characters)
            elif n==m+1:
                A[m][m+1]="-Cf"+ str(m+1)
                #A[m][m+1]=A[m][m+1].rjust(no_characters)
        max_length = max(max([len(x) for x in A[m]]),max_length)
    # Brackets for first line
    print unichr(0x250C),
    print u'{:>{width}}'.format(unichr(0x2510),width=(max_length+3)*len(A[0])+1)
        
    for row in A:
        # Leading line
        print unichr(0x2502),
        for val in row:
            print '{:{width}}'.format(val, width=max_length+2),
        # Trailing line
        print unichr(0x2502)
    # Brackets for last line
    print unichr(0x2514),
    print u'{:>{width}}'.format(unichr(0x2518),width=(max_length+3)*len(A[0])+1)
    



if __name__ == '__main__':
    main()
