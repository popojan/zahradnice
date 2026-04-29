#!/usr/bin/env python3

import re
import sys

def preprocess_sokoban_format(lines):
    """
    Convert classical one-char-per-cell Sokoban format to zahradnice two-char format.

    Classical format:
    - # = wall
    - ' ' = empty space
    - $ = box
    - . = goal
    - @ = player
    - + = player on goal
    - * = box on goal
    """
    processed_lines = []
    for line in lines:
        # Apply the conversions from soko.sh
        line = line.replace('#', '##')
        line = line.replace(' ', '  ')
        line = line.replace('$', 'st')
        line = line.replace('.', '..')
        line = line.replace('@', 'PP')
        line = line.replace('+', 'P:')
        line = line.replace('*', 'ST')
        processed_lines.append(line)
    return processed_lines


def detect_format(lines):
    """
    Detect if the input is in classical (one-char) or zahradnice (two-char) format.
    """
    # Check for typical two-char patterns
    for line in lines:
        if 'st' in line or 'PP' in line or 'ST' in line:
            return 'zahradnice'
        if '$' in line or '@' in line or '*' in line:
            return 'classical'
    return 'zahradnice'  # default


def generate_sokoban_levels(input_file, start_level, end_level,
                           auto_detect_format=True, output_dir=None,
                           total_levels=None, help_template=None):
    """
    Generate Sokoban level configuration files from a source file.

    Args:
        input_file: Path to the source file containing maze data
        start_level: Starting level number (inclusive)
        end_level: Ending level number (inclusive)
        auto_detect_format: Whether to auto-detect and convert classical format
        help_template: Template string for help directive (default: "{Collection} | Level {Number}")
    """

    # Set default help template if not provided
    if help_template is None:
        help_template = "{Collection} | Level {Number}"

    # Extract collection name from input filename
    import os
    collection_name = os.path.splitext(os.path.basename(input_file))[0]

    # Read the source file
    with open(input_file, 'r') as f:
        content = f.read()

    # Detect format and split levels accordingly
    if '---' in content:
        # Original format with --- separators
        levels = content.split('---')
        level_data = []
        for i, level_text in enumerate(levels):
            lines = level_text.strip().split('\n')
            maze_lines = []
            for line in lines:
                if line and not line.startswith(';'):
                    maze_lines.append(line.rstrip())
            if maze_lines:
                level_data.append((i, maze_lines))  # i=1 becomes level 1, i=2 becomes level 2, etc.
    else:
        # Level X format
        level_data = []
        current_level = None
        current_lines = []

        for line in content.split('\n'):
            line = line.rstrip()
            if line.startswith('Level '):
                # Save previous level if exists
                if current_level is not None and current_lines:
                    level_data.append((current_level, current_lines))

                # Start new level
                try:
                    current_level = int(line.split()[1])
                    current_lines = []
                except (IndexError, ValueError):
                    current_level = None
            elif current_level is not None and line:
                current_lines.append(line)

        # Add the last level
        if current_level is not None and current_lines:
            level_data.append((current_level, current_lines))

    # Determine digit formatting based on total levels
    if total_levels is None:
        total_levels = end_level
    digits = 3 if total_levels > 99 else 2

    # Process specified levels
    for level_num, maze_lines in level_data:
        if level_num < start_level or level_num > end_level:
            continue

        # Auto-detect format and preprocess if needed
        if auto_detect_format:
            format_type = detect_format(maze_lines)
            if format_type == 'classical':
                maze_lines = preprocess_sokoban_format(maze_lines)
                print(f"Level {level_num}: Detected classical format, converting...")

        # Find the maximum width to determine the X center
        max_width = max(len(line) for line in maze_lines)

        # Find center positions
        center_y = len(maze_lines) // 2
        center_x = max_width // 2

        # Adjust X position to be on the left of a two-char cell (even position)
        if center_x % 2 == 1:
            center_x -= 1

        # Get the character at the center position
        center_line = maze_lines[center_y] if center_y < len(maze_lines) else ""

        # Find the trigger character at the center position
        if center_x < len(center_line):
            trigger_char = center_line[center_x]
            # If it's a space, look for a better character nearby
            if trigger_char == ' ':
                # Try to find a non-space character near the center
                for offset in range(1, 10):
                    for dx in [-offset * 2, offset * 2]:  # Check even positions
                        test_x = center_x + dx
                        if 0 <= test_x < len(center_line) and center_line[test_x] not in [' ', '#']:
                            trigger_char = center_line[test_x]
                            center_x = test_x
                            break
                    if trigger_char != ' ':
                        break
        else:
            trigger_char = ' '

        # If trigger is space, use ~ (empty floor)
        if trigger_char == ' ':
            trigger_char = '~'

        # Format the maze with proper indentation and @@ markers
        formatted_maze = []
        for j, line in enumerate(maze_lines):
            if j == center_y:
                # Add @@ at beginning and @ at the center_x position
                if center_x < len(line):
                    # Replace character at center_x with @
                    line_list = list(line)
                    line_list[center_x] = '@'
                    line = ''.join(line_list)
                else:
                    # Pad the line if necessary
                    line = line.ljust(center_x + 1)
                    line = line[:center_x] + '@' + line[center_x+1:]
                formatted_line = '@@' + line
            else:
                formatted_line = '  ' + line
            formatted_maze.append(formatted_line)

        # Replicate the goal area structure (dots)
        goal_rows = []
        margin_left = max_width
        max_goal_width = 0
        buffer = []
        for row in formatted_maze:
            goal_row =      row.replace('@@', '  ')
            goal_row = goal_row.replace('@', trigger_char);
            goal_row = goal_row.replace('st', '  ')
            goal_row = goal_row.replace('ST', 'SB')
            goal_row = goal_row.replace('..', 'SB')
            goal_row = goal_row.replace('##', '  ')
            goal_row = goal_row.replace('PP', '  ')
            goal_row = goal_row.replace('P:', '  ')
            goal_row = goal_row.replace('~', ' ')
            goal_row = goal_row.rstrip()
            if goal_rows or goal_row:
                max_goal_width = max(max_goal_width, len(goal_row))
                buffer.append(goal_row)
                if goal_row:
                    margin_left = min(
                        margin_left,
                        len(goal_row) - len(goal_row.lstrip())
                    )
                    goal_rows.extend(buffer)
                    buffer = []

        for i in range(len(goal_rows)):
            goal_rows[i] = goal_rows[i][margin_left:]

        goal_rows[0] = goal_rows[0].replace('S', '@', 1);
        goal_rows[0] += ' ' * (max_goal_width - len(goal_rows[0]) - margin_left)
        goal_rows[0] += '@@'
        gone_alignment = ' ' * (max_goal_width - margin_left + 1)
        idx = goal_rows[0].index('@')
        gone_alignment = gone_alignment[:idx] + '!' + gone_alignment[idx+1:]

        # Generate help text using template
        help_text = help_template.format(Collection=collection_name, Number=level_num)

        # Create the level file content
        next_level_num = level_num + 1 if level_num < end_level else level_num
        level_content = f'''#program N level-{next_level_num:0{digits}d}.cfg
#include ../rules.cfg
#help {help_text}

# level architecture
==1T{trigger_char}
'''

        for line in formatted_maze:
            level_content += line + '\n'

        level_content += f'''
# corresponding goal
==ST 28DD 1
{gone_alignment}Done

'''
        # Join the goal pattern lines
        level_content += '\n'.join(goal_rows) + '\n'

        # Write the level file
        filename = f'{output_dir}/level-{level_num:0{digits}d}.cfg'
        with open(filename, 'w') as f:
            f.write(level_content)

        print(f'Created {filename} (trigger={trigger_char}, center=({center_x},{center_y}))')


if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python3 sokoban_level_generator_goal.py <input_file> <target_directory> [help_template]")
        print("Example: python3 sokoban_level_generator_goal.py levels.txt output/")
        print("Example: python3 sokoban_level_generator_goal.py levels.txt output/ \"{Collection} | Level {Number}\"")
        print("Default help template: \"{Collection} | Level {Number}\"")
        sys.exit(1)

    input_file = sys.argv[1]
    target_dir = sys.argv[2]
    help_template = sys.argv[3] if len(sys.argv) == 4 else None

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist")
        sys.exit(1)

    # Create target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")

    # Read the input file to detect number of levels
    with open(input_file, 'r') as f:
        content = f.read()

    # Count levels based on format
    if '---' in content:
        # Original format with --- separators
        levels = content.split('---')
        # Count non-empty sections (skip header)
        level_count = 0
        for level_text in levels:
            lines = level_text.strip().split('\n')
            maze_lines = [line for line in lines if line and not line.startswith(';')]
            if maze_lines:
                level_count += 1
    else:
        # Level X format
        import re
        level_matches = re.findall(r'^Level\s+(\d+)', content, re.MULTILINE)
        if level_matches:
            level_count = len(level_matches)
        else:
            print("Error: Could not detect level format in input file")
            sys.exit(1)

    print(f"Detected {level_count} levels in {input_file}")
    print(f"Generating levels to {target_dir}/")

    # Generate all levels
    generate_sokoban_levels(input_file=input_file,
                           start_level=1,
                           end_level=level_count,
                           auto_detect_format=True,
                           output_dir=target_dir,
                           total_levels=level_count,
                           help_template=help_template)

    print(f"Successfully generated {level_count} level files")
