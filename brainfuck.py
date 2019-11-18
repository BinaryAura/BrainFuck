import os
import sys
from time import sleep

import parsepy

import curses


STDIN_DELAY = 1


class Tape:
    def __init__(self):
        self.data = [0]
        self.low = 0

    def empty(self):
        return self.low > self.high

    @property
    def high(self):
        return self.low + len(self.data) - 1

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        if idx < self.low:  # Left of self.low
            self.data = [0] * (self.low - idx) + self.data
            self.low = idx
        elif idx > self.high:  # Right of self.high
            self.data += [0] * (idx - self.high)
        return self.data[idx - self.low]

    def __setitem__(self, idx, value):
        if idx < self.low:  # Left of self.low
            self.data = [0] * -(idx - self.low) + self.data
            self.low
        elif idx > self.high:  # Right of self.high
            self.data += [0] * (idx - self.high)
        self.data[idx - self.low] = value

    def __str__(self):
        if self.data:
            return '[' + ' '.join([str(c) for c in self.data]) + ']'
        return '[ ]'


class BF:

    lexer = parsepy.lexer.Lexer({
        "inc": r"\+",
        "dec": r"-",
        "left": r"<",
        "right": r">",
        "out": r"\.",
        "in": r",",
        "fore": r"\[",
        "back": r"\]",
        "cmt": r"[^+-.,<>\[\]]+"
    }, {"cmt": lambda t: None})

    def __init__(self, prog='', from_file=False):
        if prog:
            if from_file:
                self.file = prog
                self.load(prog, from_file)
            else:
                self.file = "<input>"
                self.load(prog, from_file)
        self.reset()
        self.inbuf = ""

    def load(self, prog, from_file=False):
        if from_file:
            self.cmds = list(BF.lexer.tokenize_file(prog))
        else:
            self.cmds = list(BF.lexer.tokenize(prog, "<input>"))

    def find_other(self, pc):

        if self.cmds[pc].type == "fore":
            dir = 1
            count = 1
        elif self.cmds[pc].type == "back":
            dir = -1
            count = -1
        else:
            return pc
        while count:
            pc += dir
            if self.cmds[pc].type == "fore":
                count += 1
            elif self.cmds[pc].type == "back":
                count -= 1
        return pc

    def getch(self):
        if not self.inbuf:
            sys.stdout.write('>? ')
            sys.stdout.flush()
            # sleep(STDIN_DELAY)
            self.inbuf += sys.stdin.readline()
        out = self.inbuf[0]
        self.inbuf = self.inbuf[1:]
        return out

    def reset(self):
        self.tape = Tape()
        self.curr = 0
        self.pc = 0

    def step(self):
        command = self.cmds[self.pc]
        if command.type == "inc":
            self.tape[self.curr] = (self.tape[self.curr] + 1) % 256
        elif command.type == "dec":
            self.tape[self.curr] = (self.tape[self.curr] - 1) % 256
        elif command.type == "left":
            self.curr -= 1
            self.tape[self.curr]
        elif command.type == "right":
            self.curr += 1
            self.tape[self.curr]
        elif command.type == "out":
            sys.stdout.write(chr(self.tape[self.curr]))
            sys.stdout.flush()
        elif command.type == "in":
            self.tape[self.curr] = ord(self.getch()) % 256
        elif command.type == "fore":
            if self.tape[self.curr] == 0:
                self.pc = self.find_other(self.pc)
        elif command.type == "back":
            if self.tape[self.curr] != 0:
                self.pc = self.find_other(self.pc)
        self.pc += 1

    def run(self):
        while self.pc < len(self.cmds):
            # print(self.tape)
            # print(" " + "  "*(self.curr - self.tape.low) + "^")
            # print(self.pc, ":", self.cmds[self.pc].token)
            # print()
            self.step()


def is_balanced(string):
    count = 0
    for ch in string:
        if ch == '[':
            count += 1
        elif ch == ']':
            count -= 1
    return count == 0


def start_interp():
    global bf
    while True:
        count = 0
        sys.stdout.write('>>> ')
        sys.stdout.flush()
        buf = sys.stdin.readline()
        if buf.strip() == "quit":
            break
        elif buf.strip() == "reset":
            bf.reset()
            continue
        elif buf.strip() == "stack":
            print(bf.tape, bf.curr)
            print(" " + "  "*(bf.curr - bf.tape.low) + "^")
            continue
        while not is_balanced(buf):
            sys.stdout.write('... ')
            sys.stdout.flush()
            buf += sys.stdin.readline()
        bf.load(buf)
        try:
            bf.run()
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt", file=sys.stderr)


def start_debug(stdscr):
    global bf
    stdscr.clear()

    stdscr.refresh()

file = None

for opt in sys.argv[1:]:
    if opt in ["-d", "--debug"]:
        debug = True
    elif opt[0] == '-':
        print("Unknown option: {}".format(sys.argv[1]), file=sys.stderr)
        print("USAGE: brainfuck.py [[-d] FILE]")
        exit(1)
    elif not file:
        if not os.path.exists(opt):
            print("File does not exist: {}".format(opt), file=sys.stderr)
            exit(2)
        file = opt
    else:
        print("Too many arguments", file=sys.stderr)
        exit(1)

bf = BF()

if debug:
    curses.wrapper(start_debug)
else:
    if file:
        bf.load(file, True)
        bf.run()
    else:
        start_interp(bf)
