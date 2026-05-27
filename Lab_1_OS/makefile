all: myshell

myshell: myshell.o utility.o
    gcc -Wall -o myshell myshell.o utility.o

myshell.o: myshell.c myshell.h
    gcc -Wall -c myshell.c

utility.o: utility.c myshell.h
    gcc -Wall -c utility.c

clean:
    rm -f *.o myshell