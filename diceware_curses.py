import argparse
import curses

arg_parser = argparse.ArgumentParser(
    description=('Create passphrase by translating dice rolls into words from '
                 'the EFF\'s large word list')
)
arg_parser.add_argument(
    '-s', '--separator',
    help=('Characters to include between words in the generated passphrase. '
          'Spaces are included automatically')
)
arg_parser.add_argument(
    '-S', '--space',
    action='store_true',
    help='Use a blank space as a separator in the passphrase'
)
arg_parser.add_argument(
    'numbers',
    nargs='+',
    help=('These numbers will be translated into words from EFF\'s large word '
          'list.')
)

# TODO Interactive mode
arg_parser.add_argument(
    '-i', '--interactive',
    action='store_true',
    help='Set this flag to work in interactive mode with a terminal UI'
)
# arg_parser.add_argument(
#     '-l', '--length',
#     help=('integer representing the number of words to include in the '
#           'passphrase'),
#     type=int
# )


def import_eff_large_wordlist(filepath):
    '''Imports EFF's large wordlist as a dict.

    Ignores lines starting with any character other than 1, 2, 3, 4, 5, or 6.

    Args:
        filepath (str): The location of the wordlist file, relative to working
            directory of execution.

    Returns:
        (dict): Dict of all number-word pairs, e.g { number: word, ... }
    '''
    dicewords = {}
    with open(filepath) as f:
        for line in f.readlines():
            # Check for number-word pair line
            if line[0] in ['1', '2', '3', '4', '5', '6']:
                number, word = line.split()
                dicewords[number] = word
            # Blank or commented line
            else:
                pass
    return dicewords


def find_word_by_num(number, word_dict):
    '''Returns the word corresponding to the provided 5-digit number.

    Args:
        number (int): number to lookup
        word_dict (dict {int: str, ...}): dict linking numbers to strings.

    If no word corresponding to the number is found, returns a placeholder.
    '''
    no_value_found_placeholder = '-----'
    try:
        return word_dict[number]
    except KeyError:
        return no_value_found_placeholder


def main(stdscr, separator, passphrase_length, digits_in_number, dicewords):
    # Curses config
    curses.curs_set(2)  # very visible

    digit_data = [[' ' for _i in range(digits_in_number)] for _j in
                  range(passphrase_length)]
    passphrase_string = ''

    # Create windows for number inputs & save to list
    spacer = 1
    input_win_height = 1
    input_win_width = digits_in_number
    input_win_uly = 2
    input_win_start_ulx = 0
    input_win_next_ulx = input_win_start_ulx

    inputs = []
    for _ in range(passphrase_length):  # 0 -> num_inputs
        current_win = curses.newwin(input_win_height, input_win_width,
                                    input_win_uly, input_win_next_ulx)
        # Window Config
        current_win.keypad(True)
        current_win.bkgd(curses.A_REVERSE)

        # Calculate next box position with spacer
        _current_uly, current_ulx = current_win.getbegyx()
        _current_height, current_width = current_win.getmaxyx()
        input_win_next_ulx = current_ulx + current_width + spacer

        # Add window to list
        inputs.append(current_win)
        # current_win.addstr('1234') # debug: show windows
        current_win.refresh()

    # Create output window
    passphrase_out = curses.newwin(1, 0, 4, 0)

    edit_number = 0
    edit_x = 0
    while True:
        # Check for space in current window
        if edit_x >= digits_in_number:
            # Move to next window
            if (edit_number + 1) < passphrase_length:
                edit_number += 1
            # Or wrap from the last window to the first if needed
            else:
                edit_number = 0
            # Start at the beginning of the window
            edit_x = 0
        # Check for need to move to previous window
        elif edit_x < 0:
            # Move to previous window
            if edit_number > 0:
                edit_number -= 1
            # Wrap to last window
            else:
                edit_number = passphrase_length - 1  # zero-index
            # Set cursor to last position in window
            edit_x = digits_in_number - 1  # zero-index

        ch = inputs[edit_number].getch(0, edit_x)

        if ch in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')]:
            digit_data[edit_number][edit_x] = chr(ch)
            # inputs[edit_number].insch(0, edit_x, ch)
            inputs[edit_number].clear()
            inputs[edit_number].insstr(0, 0, ''.join(digit_data[edit_number]))
            inputs[edit_number].refresh()
            edit_x += 1

            # Print match, if possible
            # TODO Make more pythonic or abstract into function
            passphrase_out.clear()
            passphrase_array = []
            for digit_array in digit_data:
                number = ''.join(digit_array)
                word = find_word_by_num(number, dicewords)
                passphrase_array.append(word)
            passphrase_string = separator.join(passphrase_array)

            # passphrase_string = separator.join(
            #     [find_word_by_num(''.join(number), dicewords) for number in
            #      digit_data])
            passphrase_out.addstr(passphrase_string)
            passphrase_out.refresh()

        elif ch == curses.KEY_LEFT:
            edit_x -= 1
        elif ch == curses.KEY_RIGHT:
            edit_x += 1
        # TODO Backspace key
        # elif ch == curses.KEY_BACKSPACE:
        elif ch == ord('q'):
            return passphrase_string


if __name__ == '__main__':
    args = arg_parser.parse_args()

    # TODO allow setting via argparse if in interactive mode
    passphrase_length = 6

    # TODO Better args for separators and spacers
    # Use default separator if none specified
    if args.separator is None and args.space is False:
        separator = ''
    elif args.separator is None and args.space is True:
        separator = ' '
    elif args.separator and args.space is True:
        separator = ' {} '.format(args.separator)
    else:
        separator = args.separator

    # Import EFF large word list
    dicewords = import_eff_large_wordlist('eff_large_wordlist.txt')

    # CLI Args mode
    if args.interactive is False:
        dice_roll_numbers = args.numbers
        words = []
        try:
            for number in dice_roll_numbers:
                words.append(find_word_by_num(number, dicewords))
            passphrase = separator.join(words)
            print(passphrase)
        except KeyError:
            print('Error: Could not find {} in EFF large wordlist'
                  .format(number))

    # Interactive mode
    else:
        passphrase = curses.wrapper(main, separator, passphrase_length,
                                    5, dicewords)
        print(passphrase)
