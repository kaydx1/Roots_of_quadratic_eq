from __future__ import print_function
import tokenize
import sys
import io
from collections import deque
from math import sqrt

# Исходная программа
# text = ''': power2 dup * ;
# : get_arg print read cast_int ;

# "Give me $a" get_arg "a" store
# "Give me $b" get_arg "b" store
# "Give me $c" get_arg "c" store
# "Give me $x" get_arg "x" store
# "a" load "x" load * "b" load + "x" load * "c" load + dup println stack'''

# Вычисление действительных корней квадратного уравнения
text = ''': power2 dup * ;
:power3 dup dup * * ;
: get_arg print read cast_int ;

"Give me $a" get_arg "a" store
"Give me $b" get_arg "b" store
"Give me $c" get_arg "c" store
"b" load power2 4 "a" load "c" load * * -
"D" store
0 "D" load >=
"b" load change "D" load squareroot + "a" load 2 * / cast_str " " + "b" load change "D" load squareroot - "a" load 2 * / cast_str +
"D<0"
if
println
stack'''


def parse(text):

    stream = io.StringIO(text)
    tokens = tokenize.generate_tokens(stream.readline)

    for toknum, tokval, _, _, _ in tokens:
        if toknum == tokenize.NUMBER:
            yield int(tokval)
        else:
            yield tokval


code = list(parse(text))

code = [oper for oper in code if oper != "\n" and oper != ""]


def remove_proc(code):
    pointer = 0
    tmplist = []
    tmpdict = {}
    while pointer < len(code):
        if code[pointer] == ':':
            name = code[pointer+1]
            code.pop(pointer)
            code.pop(pointer)
            while code[pointer] != ";":
                tmplist.append(code[pointer])
                code.pop(pointer)
            code.pop(pointer)
            pointer -= 1
            tmpdict[name] = tmplist
            tmplist = []

        pointer += 1

    return tmpdict


tmdict = remove_proc(code)

# Добавляем return в конец процедуры
for i in tmdict:
    array = tmdict[i]
    array.append('return')
    tmdict[i] = array

# Добавляем exit в конец
code.append('exit')

for index, value in enumerate(code):
    if value in tmdict:
        code.insert(index+1, "call")


for key in tmdict:
    if key in code:
        code.extend(tmdict[key])
        for index, value in enumerate(code):
            if value == key:
                # Находим адрес процедуры с конца массива
                code[index] = len(code) - len(tmdict[key])


class Stack(deque):
    push = deque.append

    def top(self):
        return self[-1]


class Machine:
    def __init__(self, code):
        self.data_stack = Stack()
        self.return_stack = Stack()
        self.instruction_pointer = 0
        self.code = code
        self.heap = {}

    def pop(self):
        return self.data_stack.pop()

    def push(self, value):
        self.data_stack.push(value)

    def top(self):
        return self.data_stack.top()

    def run(self):
        while self.instruction_pointer < len(self.code):
            opcode = self.code[self.instruction_pointer]
            self.instruction_pointer += 1
            self.dispatch(opcode)

    def dispatch(self, op):
        dispatch_map = {
            "%":        self.mod,
            "*":        self.mul,
            "+":        self.plus,
            "-":        self.minus,
            "/":        self.div,
            "==":       self.eq,
            ">=":        self.bigger,
            "cast_int": self.cast_int,
            "cast_str": self.cast_str,
            "drop":     self.drop,
            "dup":      self.dup,
            "exit":     self.exit,
            "if":       self.if_stmt,
            "jmp":      self.jmp,
            "over":     self.over,
            "print":    self.print,
            "println":  self.println,
            "read":     self.read,
            "stack":    self.dump_stack,
            "swap":     self.swap,
            "store":     self.store,
            "call":     self.call,
            "return":   self.retorn,
            "load": self.load,
            "change":   self.change,
            "squareroot":   self.squareroot
        }

        if op in dispatch_map:
            dispatch_map[op]()
        elif isinstance(op, int):
            self.push(op)
        elif isinstance(op, str) and op[0] == op[-1] == '"':
            self.push(op[1:-1])
        else:
            self.push(op)

    # Операции
    def squareroot(self):
        discr = self.pop()
        if discr < 0:
            raise RuntimeError("D<0")
        else:
            self.push(sqrt(discr))

    def change(self):
        self.push(self.pop() * (-1))

    def bigger(self):
        self.push(self.pop() >= self.pop())

    def plus(self):
        self.push(self.pop() + self.pop())

    def exit(self):
        sys.exit(0)

    def minus(self):
        last = self.pop()
        self.push(self.pop() - last)

    def mul(self):
        self.push(self.pop() * self.pop())

    def div(self):
        last = self.pop()
        self.push(self.pop() / last)

    def mod(self):
        last = self.pop()
        self.push(self.pop() % last)

    def dup(self):
        self.push(self.top())

    def over(self):
        b = self.pop()
        a = self.pop()
        self.push(a)
        self.push(b)
        self.push(a)

    def drop(self):
        self.pop()

    def swap(self):
        b = self.pop()
        a = self.pop()
        self.push(b)
        self.push(a)

    def print(self):
        sys.stdout.write(str(self.pop()))
        sys.stdout.flush()

    def println(self):
        sys.stdout.write("%s\n" % self.pop())
        sys.stdout.flush()

    def read(self):
        self.push(input())

    def cast_int(self):
        self.push(int(self.pop()))

    def cast_str(self):
        self.push(str(self.pop()))

    def eq(self):
        self.push(self.pop() == self.pop())

    def if_stmt(self):
        false_clause = self.pop()
        true_clause = self.pop()
        test = self.pop()
        self.push(true_clause if test else false_clause)

    def jmp(self):
        addr = self.pop()
        if isinstance(addr, int) and 0 <= addr < len(self.code):
            self.instruction_pointer = addr
        else:
            raise RuntimeError("JMP address must be a valid integer.")

    def dump_stack(self):
        print("Data stack (top first):")

        for v in reversed(self.data_stack):
            print(" - type %s, value '%s'" % (type(v), v))

    def store(self):
        var_name = self.pop()
        var_value = self.pop()
        self.heap[var_name] = var_value

    def call(self):
        self.return_stack.push(self.instruction_pointer)
        self.jmp()

    def retorn(self):
        self.instruction_pointer = self.return_stack.pop()

    def load(self):
        var = self.pop()
        value = self.heap[var]
        self.push(value)


m = Machine(code)
m.run()
