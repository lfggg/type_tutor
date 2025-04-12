import curses
import time
import os

# -------------------------------------------------------------------------
# 1) DEFAULT TEXT
# -------------------------------------------------------------------------
DEFAULT_TEXT = """\
The Buddha’s first teaching was called the Dhammacakkappavattana
Shift ' test: "
"""

# -------------------------------------------------------------------------
# 2) READ WORDS FROM FILE OR USE DEFAULT
#    Also replace curly quotes with straight quotes
# -------------------------------------------------------------------------
def read_words_from_file(filename):
    if filename:
        file_path = os.path.join(os.getcwd(), filename)
        print(f"DEBUG: Checking file at {file_path}")
        if os.path.isfile(file_path):
            print("DEBUG: File found. Attempting to read...")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.strip()
            if not content:
                print("DEBUG: File is empty or whitespace. Using default text.")
                content = DEFAULT_TEXT
            else:
                print("DEBUG: Successfully read file.")
        else:
            print("DEBUG: File not found. Using default text.")
            content = DEFAULT_TEXT
    else:
        print("DEBUG: No filename given. Using default text.")
        content = DEFAULT_TEXT

    # Replace curly quotes with ASCII
    content = content.replace("’", "'").replace("‘", "'")

    return content.split()

# -------------------------------------------------------------------------
# 3) CHUNK WORDS
# -------------------------------------------------------------------------
def chunk_words(words, chunk_size=8):
    for i in range(0, len(words), chunk_size):
        yield words[i : i + chunk_size]

# -------------------------------------------------------------------------
# 4) KEYBOARD LAYOUT (with offset for more realistic alignment)
# -------------------------------------------------------------------------
ROW_SPECS = [
    (0, [
       ('~',5), ('1',3), ('2',3), ('3',3), ('4',3), ('5',3),
       ('6',3), ('7',3), ('8',3), ('9',3), ('0',3), ('-',3),
       ('=',3), ('Bksp',5)
    ]),
    (2, [
       ('Tab',5), ('Q',3), ('W',3), ('E',3), ('R',3), ('T',3),
       ('Y',3), ('U',3), ('I',3), ('O',3), ('P',3), ('[',3),
       (']',3), ('\\',3)
    ]),
    (4, [
       ('Caps',5), ('A',3), ('S',3), ('D',3), ('F',3), ('G',3),
       ('H',3), ('J',3), ('K',3), ('L',3), (';',3), ("'",3),
       ('Enter',5)
    ]),
    (5, [
       ('Shift',6), ('Z',3), ('X',3), ('C',3), ('V',3), ('B',3),
       ('N',3), ('M',3), (',',3), ('.',3), ('/',3), ('Shift',6)
    ]),
    # Bottom row with bigger offset, longer space
    (8, [
       ('Ctrl',4), ('Alt',3), ('Space',15), ('Alt',3), ('Ctrl',4)
    ])
]

# SHIFT combos
SHIFT_COMBOS = {
   ('Shift','`'): '~',
   ('Shift','1'): '!',
   ('Shift','2'): '@',
   ('Shift','3'): '#',
   ('Shift','4'): '$',
   ('Shift','5'): '%',
   ('Shift','6'): '^',
   ('Shift','7'): '&',
   ('Shift','8'): '*',
   ('Shift','9'): '(',
   ('Shift','0'): ')',
   ('Shift','-'): '_',
   ('Shift','='): '+',
   ('Shift','q'): 'Q',
   ('Shift','w'): 'W',
   ('Shift','e'): 'E',
   ('Shift','r'): 'R',
   ('Shift','t'): 'T',
   ('Shift','y'): 'Y',
   ('Shift','u'): 'U',
   ('Shift','i'): 'I',
   ('Shift','o'): 'O',
   ('Shift','p'): 'P',
   ('Shift','a'): 'A',
   ('Shift','s'): 'S',
   ('Shift','d'): 'D',
   ('Shift','f'): 'F',
   ('Shift','g'): 'G',
   ('Shift','h'): 'H',
   ('Shift','j'): 'J',
   ('Shift','k'): 'K',
   ('Shift','l'): 'L',
   ('Shift','z'): 'Z',
   ('Shift','x'): 'X',
   ('Shift','c'): 'C',
   ('Shift','v'): 'V',
   ('Shift','b'): 'B',
   ('Shift','n'): 'N',
   ('Shift','m'): 'M',
   ('Shift','['): '{',
   ('Shift',']'): '}',
   ('Shift','\\'): '|',
   ('Shift',';'): ':',
   ('Shift',"\'"): '"',
   ('Shift',','): '<',
   ('Shift','.'): '>',
   ('Shift','/'): '?',
}

KEY_LAYOUT = {}  # label -> list of (y, x, width)

def draw_key_box(stdscr, y, x, label, width, color_pair):
    top_line = "┌" + "─"*width + "┐"
    mid_line = "│" + label.center(width) + "│"
    bot_line = "└" + "─"*width + "┘"
    stdscr.attron(curses.color_pair(color_pair))
    stdscr.addstr(y,   x, top_line)
    stdscr.addstr(y+1, x, mid_line)
    stdscr.addstr(y+2, x, bot_line)
    stdscr.attroff(curses.color_pair(color_pair))

def build_keyboard_layout(start_y):
    KEY_LAYOUT.clear()
    current_y = start_y
    for (offset, row_keys) in ROW_SPECS:
        current_x = offset
        for (label, width) in row_keys:
            KEY_LAYOUT.setdefault(label, [])
            KEY_LAYOUT[label].append((current_y, current_x, width))
            current_x += (width + 2) + 1  # box + 1 space
        current_y += 3 + 1  # each row is 3 lines + spacing

def draw_full_keyboard(stdscr):
    for label, positions in KEY_LAYOUT.items():
        for (y, x, width) in positions:
            draw_key_box(stdscr, y, x, label, width, 1)

def highlight_key(stdscr, label, color_pair):
    if label not in KEY_LAYOUT:
        return
    for (y, x, width) in KEY_LAYOUT[label]:
        draw_key_box(stdscr, y, x, label, width, color_pair)

# -------------------------------------------------------------------------
# 5) SHIFT / COMBO LOGIC
# -------------------------------------------------------------------------
def get_char_from_keys(pressed_keys):
    pset = set(k.lower() for k in pressed_keys)
    for (sh, base_char), result in SHIFT_COMBOS.items():
        if sh.lower() in pset and base_char.lower() in pset:
            return result
    if len(pset) == 1:
        single = list(pset)[0]
        if single == 'space':
            return ' '
        return single
    return None

def is_correct_char_needed(next_char, typed_char):
    return (typed_char == next_char)

# -------------------------------------------------------------------------
# 6) TYPING PRACTICE
#    Stacking typed text *directly* beneath the target text
#    so that each character lines up for easy comparison.
# -------------------------------------------------------------------------
def typing_practice(stdscr, words):
    curses.curs_set(0)
    stdscr.clear()

    max_y, max_x = stdscr.getmaxyx()

    # Position the keyboard at the bottom
    total_rows = len(ROW_SPECS)
    keyboard_height = total_rows * 4  # each row: 3 lines + 1 spacing
    keyboard_top_y = max_y - keyboard_height

    build_keyboard_layout(keyboard_top_y)
    word_sets = list(chunk_words(words, 8))
    set_index = 0

    # We'll display:
    #   line 0 => "TYPE THIS:" label
    #   line 1 => target_str
    #   line 2 => typed_str
    # Then the keyboard is at the bottom.
    while set_index < len(word_sets):
        current_set = word_sets[set_index]
        target_str = " ".join(current_set)
        typed_str = ""

        stdscr.clear()
        # Show label
        stdscr.addstr(0, 0, "TYPE THIS:", curses.A_BOLD | curses.A_UNDERLINE)
        # Show the text to be typed on line 1
        stdscr.addstr(1, 0, target_str, curses.A_BOLD)
        # The typed text goes on line 2, directly beneath

        draw_full_keyboard(stdscr)
        pressed_keys = set()

        while typed_str != target_str:
            # Update the typed text
            stdscr.addstr(2, 0, " " * max_x)  # clear old typed text
            stdscr.addstr(2, 0, typed_str)

            # Next char
            next_char = target_str[len(typed_str)]
            required_keys = []

            # Determine needed keys
            if next_char == ' ':
                required_keys = ["Space"]
            else:
                found_combo = False
                for (sh, base_char), result in SHIFT_COMBOS.items():
                    if result == next_char:
                        required_keys = [sh, base_char]
                        found_combo = True
                        break
                if not found_combo and next_char.isalpha() and next_char.isupper():
                    required_keys = ["Shift", next_char.lower()]
                elif not found_combo and not next_char.isspace():
                    required_keys = [next_char]

            # Redraw keyboard, highlight needed
            draw_full_keyboard(stdscr)
            for rk in required_keys:
                highlight_key(stdscr, rk.capitalize(), 2)

            stdscr.refresh()
            ch = stdscr.getch()
            if ch == 27:  # ESC => quit
                return
            elif ch in (curses.KEY_BACKSPACE, 127):
                if len(typed_str) > 0:
                    typed_str = typed_str[:-1]
                pressed_keys.clear()
                continue
            else:
                try:
                    c = chr(ch)
                except:
                    c = ''
                if c.isalpha():
                    if c.isupper():
                        pressed_keys.add("Shift")
                        pressed_keys.add(c.lower())
                    else:
                        pressed_keys.add(c)
                elif c == ' ':
                    pressed_keys.add("Space")
                else:
                    pressed_keys.add(c)

            # highlight pressed
            draw_full_keyboard(stdscr)
            for rk in required_keys:
                highlight_key(stdscr, rk.capitalize(), 2)
            for pk in pressed_keys:
                highlight_key(stdscr, pk.capitalize(), 3)

            stdscr.refresh()
            time.sleep(0.03)

            typed_char = get_char_from_keys(pressed_keys)
            if typed_char is not None:
                if is_correct_char_needed(next_char, typed_char):
                    typed_str += typed_char
                    # highlight pressed in green
                    for pk in pressed_keys:
                        highlight_key(stdscr, pk.capitalize(), 10)
                    stdscr.refresh()
                    time.sleep(0.1)
                else:
                    curses.beep()
                    for pk in pressed_keys:
                        highlight_key(stdscr, pk.capitalize(), 9)
                    stdscr.refresh()
                    time.sleep(0.3)
                pressed_keys.clear()

        set_index += 1
        # After each chunk
        stdscr.addstr(4, 0, "Great job! Press any key for next set...", curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()

    # All done
    stdscr.clear()
    stdscr.addstr(0, 0, "All sets completed! Press any key to exit.", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

# -------------------------------------------------------------------------
# 7) MAIN: curses wrapper
# -------------------------------------------------------------------------
def run_curses_app(stdscr, words):
    curses.start_color()
    curses.use_default_colors()
    # color pairs:
    #   1 = default
    #   2 = needed highlight (blue on white)
    #   3 = pressed highlight (magenta on white)
    #   9 = red highlight
    #   10= green highlight
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
    curses.init_pair(9, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_WHITE)

    typing_practice(stdscr, words)

def main():
    print("Optionally enter a text filename (in this folder), or press ENTER for default:")
    filename = input("> ").strip()
    if not filename:
        filename = None
    words = read_words_from_file(filename)
    curses.wrapper(run_curses_app, words)

if __name__ == "__main__":
    main()
