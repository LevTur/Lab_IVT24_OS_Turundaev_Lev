#!/usr/bin/env python3
import os
import sys
import subprocess
import shlex

def parse_line(line):
    """Разбор командной строки с учётом кавычек и спецсимволов."""
    return shlex.split(line)

def handle_redirection(args):
    """
    Обработка перенаправления ввода-вывода.
    Возвращает (cmd_args, stdin_file, stdout_file, append_mode).
    """
    cmd_args = []
    stdin_file = None
    stdout_file = None
    append_mode = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '<' and i + 1 < len(args):
            stdin_file = args[i + 1]
            i += 2
        elif arg == '>' and i + 1 < len(args):
            stdout_file = args[i + 1]
            append_mode = False
            i += 2
        elif arg == '>>' and i + 1 < len(args):
            stdout_file = args[i + 1]
            append_mode = True
            i += 2
        else:
            cmd_args.append(arg)
            i += 1
    return cmd_args, stdin_file, stdout_file, append_mode

def is_internal(cmd):
    return cmd in ('cd', 'clr', 'dir', 'environ', 'echo', 'help', 'pause', 'quit')

def run_internal(cmd, args, env):
    if cmd == 'cd':
        directory = args[0] if args else None
        if directory is None:
            print(os.getcwd())
        else:
            try:
                os.chdir(directory)
                env['PWD'] = os.getcwd()
            except FileNotFoundError:
                print(f"myshell: cd: {directory}: No such file or directory")
    elif cmd == 'clr':
        print("\033c", end="")
    elif cmd == 'dir':
        directory = args[0] if args else '.'
        try:
            for entry in os.listdir(directory):
                print(entry)
        except FileNotFoundError:
            print(f"myshell: dir: {directory}: No such file or directory")
    elif cmd == 'environ':
        for k, v in env.items():
            print(f"{k}={v}")
    elif cmd == 'echo':
        comment = " ".join(args)
        print(comment)
    elif cmd == 'help':
        print("Simple shell myshell. Supported commands:")
        print("cd [directory]      — change directory")
        print("clr                 — clear screen")
        print("dir [directory]     — list directory contents")
        print("environ             — show environment variables")
        print("echo <comment>      — print comment")
        print("help                — this help")
        print("pause               — wait for Enter")
        print("quit                — exit shell")
    elif cmd == 'pause':
        input("Press Enter to continue...")
    elif cmd == 'quit':
        sys.exit(0)

def main():
    shell_path = os.path.abspath(sys.argv[0])
    env = os.environ.copy()
    env['shell'] = shell_path

    batch_mode = len(sys.argv) > 1
    if batch_mode:
        try:
            with open(sys.argv[1], 'r') as f:
                batch_lines = f.readlines()
        except FileNotFoundError:
            print(f"myshell: batch file '{sys.argv[1]}' not found")
            return
    else:
        batch_lines = None

    line_index = 0
    while True:
        try:
            if batch_mode:
                if line_index >= len(batch_lines):
                    break
                line = batch_lines[line_index].strip()
                line_index += 1
                if not line:
                    continue
            else:
                try:
                    line = input(f"{os.getcwd()} $ ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

            if not line:
                continue

            # Проверка фонового выполнения
            background = line.rstrip().endswith('&')
            if background:
                line = line.rstrip()[:-1].rstrip()

            args = parse_line(line)
            if not args:
                continue

            cmd, *params = args

            # Перенаправление ввода-вывода
            cmd_args, stdin_file, stdout_file, append_mode = handle_redirection(params)

            if is_internal(cmd):
                # Перенаправление для внутренних команд
                old_in, old_out = None, None
                try:
                    if stdin_file:
                        old_in = sys.stdin.fileno()
                        sys.stdin = open(stdin_file, 'r')
                    if stdout_file:
                        mode = 'a' if append_mode else 'w'
                        old_out = sys.stdout.fileno()
                        sys.stdout = open(stdout_file, mode)
                    run_internal(cmd, cmd_args, env)
                finally:
                    if old_in is not None:
                        sys.stdin.close()
                        sys.stdin = os.fdopen(old_in, 'r')
                    if old_out is not None:
                        sys.stdout.close()
                        sys.stdout = os.fdopen(old_out, 'w')
            else:
                # Внешние команды с поддержкой фонового режима и перенаправления
                proc_env = env.copy()
                proc_env['parent'] = shell_path

                stdin_fh = open(stdin_file, 'r') if stdin_file else None
                mode = 'a' if append_mode else 'w'
                stdout_fh = open(stdout_file, mode) if stdout_file else None

                proc = subprocess.Popen(
                    [cmd] + cmd_args,
                    env=proc_env,
                    stdin=stdin_fh,
                    stdout=stdout_fh,
                    stderr=subprocess.STDOUT,
                    text=True,
                    start_new_session=True  # для корректного фонового выполнения
                )

                if not background:
                    proc.wait()

                if stdin_fh:
                    stdin_fh.close()
                if stdout_fh:
                    stdout_fh.close()

        except Exception as e:
            print(f"myshell: error: {e}")
