# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import json

from todo.utils.styles import Fore, Style


class Command(object):
    """
    Base class for all CLI commands

    This class provides:
    - Common file I/O operations (read/write todos.json)
    - Priority management (validation, colors, symbols)
    - User interaction helpers (input parsing, confirmations)
    - Data manipulation (todo creation, updates)

    All specific commands (Add, List, Toggle, etc.) inherit from this class
    """

    def __init__(self, project_file='todos.json'):
        """
        Initialize command with project file path

        Args:
            project_file (str): Path to todos.json file
                               Example: 'todos.json' or './data/todos.json'
        """
        self.PROJECT_FILE = project_file

        # Default project name when none is set
        self.UNTITLED_NAME = 'Untitled'

        # Valid priority levels - only these are accepted
        self.PRIORITY_LEVELS = ['low', 'medium', 'high']

        # Default priority when none is specified
        self.DEFAULT_PRIORITY = 'medium'

    def run(self):
        """
        Main method to execute the command

        Must be overridden by subclasses

        Raises:
            NotImplementedError: If subclass doesn't implement this method
        """
        raise NotImplementedError

    # ============================================================================
    # PRIORITY MANAGEMENT METHODS
    # ============================================================================

    def validate_priority(self, priority):
        """
        Validates if priority is a valid level

        This ensures only recognized priority levels are used in the system.

        Args:
            priority (str): Priority level to validate
                           Examples: 'high', 'MEDIUM', 'Low'

        Returns:
            str: Lowercase priority string if valid
                 Example: 'HIGH' → 'high'

        Raises:
            ValueError: If priority is not in PRIORITY_LEVELS
                       Example: validate_priority('urgent')
                               → ValueError: "Invalid priority: urgent..."

        Example:
            >>> validate_priority('HIGH')
            'high'

            >>> validate_priority('medium')
            'medium'

            >>> validate_priority('URGENT')
            ValueError: Invalid priority: urgent. Must be one of: low, medium, high

        Logic:
            1. Convert input to lowercase for case-insensitive comparison
            2. Check if it exists in PRIORITY_LEVELS list
            3. If valid, return lowercase version
            4. If invalid, raise descriptive error with valid options
        """
        priority_lower = priority.lower()

        if priority_lower not in self.PRIORITY_LEVELS:
            raise ValueError(
                'Invalid priority: {priority}. Must be one of: {valid_priorities}'.format(
                    priority=priority,
                    valid_priorities=', '.join(self.PRIORITY_LEVELS)
                )
            )

        return priority_lower

    def get_priority_color(self, priority):
        """
        Maps priority level to terminal color code

        This provides visual distinction in terminal output using ANSI colors.

        Args:
            priority (str): Priority level
                           Must be one of: 'low', 'medium', 'high'

        Returns:
            str: ANSI color code from Fore object
                 Examples: Fore.FAIL (red), Fore.WARNING (yellow), Fore.OK (green)

        Color Scheme:
            high   → Fore.FAIL (red)       - ⚠️ Demands immediate attention
            medium → Fore.WARNING (yellow) - ⚠️ Moderate importance
            low    → Fore.OK (green)       - ✓ Can wait, less urgent

        Example:
            >>> get_priority_color('high')
            '\x1b[91m'  # Red ANSI code

            >>> get_priority_color('low')
            '\x1b[92m'  # Green ANSI code

        Logic:
            1. Create dictionary mapping priority → color
            2. Look up priority in dictionary
            3. Return color code
            4. Default to Fore.GREEN if priority not found (backward compatibility)
        """
        priority_colors = {
            'high': Fore.FAIL,      # Red - high priority gets red
            'medium': Fore.WARNING,  # Yellow - medium gets yellow
            'low': Fore.GREEN       # Green - low priority is calm
        }

        # Return color, or Fore.GREEN if priority not in dict
        return priority_colors.get(priority, Fore.GREEN)

    def get_priority_symbol(self, priority):
        """
        Returns visual symbol representing priority level

        Text symbols for quick visual scanning without relying on colors.
        Useful for terminals that don't support colors well.

        Args:
            priority (str): Priority level
                           Must be one of: 'low', 'medium', 'high'

        Returns:
            str: Visual symbol as string
                 Examples: '!!!', '~~', '--'

        Symbol Meanings:
            '!!!' → high   - Three exclamation marks = URGENT
            '~~ → medium - Tildes = moderate concern
            '--' → low    - Dashes = less important

        Example:
            >>> get_priority_symbol('high')
            '!!!'

            >>> get_priority_symbol('low')
            '--'

            # Output example:
            # 1. !!! [ ] Fix critical bug
            # 2. ~~  [ ] Update documentation
            # 3. --  [ ] Clean up code

        Logic:
            1. Create dictionary mapping priority → symbol
            2. Look up priority in dictionary
            3. Return symbol
            4. Default to '--' if priority not found
        """
        priority_symbols = {
            'high': '!!!',    # Three exclamation marks for urgency
            'medium': '~~',   # Tildes for moderate
            'low': '--'       # Dashes for low priority
        }

        # Return symbol, or '--' as default
        return priority_symbols.get(priority, '--')

    def get_priority_icon(self, priority):
        """
        Returns emoji-like icon for priority level

        An alternative visual representation using characters.

        Args:
            priority (str): Priority level

        Returns:
            str: Icon character
                 Examples: '🔴' (red), '🟡' (yellow), '🟢' (green)

        Example:
            >>> get_priority_icon('high')
            '🔴'

        Logic:
            1. Map priority to appropriate character
            2. Return character
            3. Default to neutral icon
        """
        priority_icons = {
            'high': '🔴',      # Red circle - urgent
            'medium': '🟡',    # Yellow circle - moderate
            'low': '🟢'        # Green circle - low priority
        }

        return priority_icons.get(priority, '⭕')

    # ============================================================================
    # FILE I/O METHODS
    # ============================================================================

    def read_project_file(self):
        """
        Reads and parses todos.json file

        Returns:
            dict or None: Parsed JSON data if file exists
                         None if file doesn't exist

        File Format (todos.json):
            {
                "name": "My Project",
                "todos": [
                    {
                        "done": false,
                        "title": "Buy milk",
                        "priority": "high"
                    },
                    {
                        "done": true,
                        "title": "Do laundry",
                        "priority": "medium"
                    }
                ]
            }

        Example:
            >>> data = read_project_file()
            >>> data['name']
            'My Project'
            >>> len(data['todos'])
            2

        Logic:
            1. Try to open PROJECT_FILE
            2. Parse JSON content
            3. Return parsed data
            4. If file not found, return None
            5. If JSON invalid, raise error
        """
        try:
            with open(self.PROJECT_FILE, 'r', encoding='utf-8') as project_file:
                data = json.load(project_file)
            return data
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            print(
                '{fail}Error: todos.json is corrupted (invalid JSON){reset}'.format(
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL
                )
            )
            sys.exit(1)

    def update_project(self, new_data):
        """
        Writes updated data back to todos.json

        This is how all changes are persisted to disk.

        Args:
            new_data (dict): Data to write to file
                            Should contain 'name' and 'todos' keys

        File Operations:
            1. Convert Python dict to JSON string
            2. Write to PROJECT_FILE
            3. Format with indentation for readability
            4. Use UTF-8 encoding for international characters

        Example:
            >>> new_data = {
            ...     'name': 'My Project',
            ...     'todos': [
            ...         {'done': False, 'title': 'Task 1', 'priority': 'high'}
            ...     ]
            ... }
            >>> update_project(new_data)
            # Now todos.json contains this data

        JSON Output Format:
            {
                "name": "My Project",
                "todos": [
                    {
                        "done": false,
                        "priority": "high",
                        "title": "Task 1"
                    }
                ]
            }

        Logic:
            1. Try to open file for writing
            2. Use json.dump() to serialize data
            3. Use sort_keys=True for consistent ordering
            4. Use indent=4 for readability
            5. Use ensure_ascii=False to support emojis/unicode
            6. If write fails, show error and exit
        """
        try:
            with open(self.PROJECT_FILE, 'w', encoding='utf-8') as project_file:
                json.dump(
                    new_data,
                    project_file,
                    sort_keys=True,          # Alphabetical order for consistency
                    indent=4,                # 4 spaces for readability
                    ensure_ascii=False,      # Support Unicode characters
                )
        except IOError as err:
            print(
                '{fail}Error writing to {file}: {error}{reset}'.format(
                    fail=Fore.FAIL,
                    file=self.PROJECT_FILE,
                    error=str(err),
                    reset=Style.RESET_ALL
                )
            )
            sys.exit(1)

    # ============================================================================
    # DATA EXTRACTION METHODS
    # ============================================================================

    def get_project_name(self):
        """
        Retrieves the project name from todos.json

        Returns:
            str: Project name, or UNTITLED_NAME if not set

        Example:
            >>> get_project_name()
            'My Fitness Tracker'

            # If name is empty or missing:
            >>> get_project_name()
            'Untitled'

        Logic:
            1. Read project file
            2. If file doesn't exist, return default name
            3. Extract 'name' field
            4. If name is empty, return default
            5. Otherwise return the name
        """
        data = self.read_project_file()

        if data is None:
            return self.UNTITLED_NAME

        name = data.get('name', '')
        return name if name else self.UNTITLED_NAME

    def get_todos_list(self):
        """
        Retrieves all todos from todos.json

        Returns:
            list: List of todo dictionaries, or empty list if none exist

        Todo Dictionary Format:
            {
                "done": bool,           # Completion status
                "title": str,          # Task description
                "priority": str        # 'low', 'medium', or 'high'
            }

        Example:
            >>> todos = get_todos_list()
            >>> todos[0]
            {'done': False, 'title': 'Buy milk', 'priority': 'high'}

            >>> len(todos)
            5

        Logic:
            1. Read project file
            2. If file doesn't exist, return empty list
            3. Extract 'todos' field
            4. If field missing or not a list, return empty list
            5. Add 'priority' field to todos that don't have it (backward compat)
        """
        data = self.read_project_file()

        if data is None:
            return []

        todos = data.get('todos', [])

        # Backward compatibility: add priority to old todos
        for todo in todos:
            if 'priority' not in todo:
                todo['priority'] = self.DEFAULT_PRIORITY

        return todos if isinstance(todos, list) else []

    def get_command_attributes(self):
        """
        Extracts all arguments after the command name from sys.argv

        Example Scenarios:
            Command typed: todo add "Buy milk" --priority=high
            sys.argv: ['todo', 'add', 'Buy milk', '--priority=high']
            Returns: "Buy milk --priority=high"

            Command typed: todo list
            sys.argv: ['todo', 'list']
            Returns: None (or empty string)

        Returns:
            str: Space-separated string of all arguments
            None: If no arguments provided

        Logic:
            1. Access sys.argv[2:] (skip program name and command)
            2. Join all elements with spaces
            3. Return joined string
            4. If empty, return None
        """
        try:
            # sys.argv[0] = program name (todo)
            # sys.argv[1] = command name (add, list, etc.)
            # sys.argv[2:] = all arguments
            attributes = sys.argv[2:]
            if attributes:
                return ' '.join(attributes)
            return None
        except (IndexError, AttributeError):
            return None

    def get_titles_input(self):
        """
        Parses comma-separated task titles from command-line input

        Allows users to add multiple tasks in one command

        Example Scenarios:
            Input: "Buy milk, Do laundry, Call mom"
            Output: ['Buy milk', 'Do laundry', 'Call mom']

            Input: "Fix bug"
            Output: ['Fix bug']

            Input: "Item 1,   Item 2  ,  Item 3"  # Extra spaces
            Output: ['Item 1', 'Item 2', 'Item 3']

        Returns:
            list: List of stripped title strings

        Raises:
            SystemExit: If no input provided (exits with error)

        Logic:
            1. Get command attributes
            2. If empty, show error and exit
            3. Split by comma
            4. Strip whitespace from each item
            5. Filter out empty items
            6. Return list of titles
        """
        titles_input = self.get_command_attributes()

        if not titles_input:
            print(
                '{fail}Error: No input provided{reset}'.format(
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL
                )
            )
            sys.exit(1)

        # Split by comma
        titles = titles_input.split(',')

        # Strip whitespace and filter empty strings
        cleaned_titles = [
            title.strip()
            for title in titles
            if title.strip()
        ]

        if not cleaned_titles:
            print(
                '{fail}Error: No valid input after parsing{reset}'.format(
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL
                )
            )
            sys.exit(1)

        return cleaned_titles

    # ============================================================================
    # TODO CREATION METHODS
    # ============================================================================

    def create_todo_item(self, title, priority='medium'):
        """
        Creates a new todo item dictionary

        A todo item is the basic unit of the system. This method ensures
        all new items have the correct structure and valid data.

        Args:
            title (str): Task description
                        Examples: 'Buy milk', 'Fix critical bug'
            priority (str): Priority level (default: 'medium')
                           Must be one of: 'low', 'medium', 'high'

        Returns:
            dict: Todo item dictionary with all required fields
                 Structure:
                 {
                     'done': False,
                     'title': str,
                     'priority': str
                 }

        Example:
            >>> create_todo_item('Buy milk', 'high')
            {
                'done': False,
                'title': 'Buy milk',
                'priority': 'high'
            }

            >>> create_todo_item('Read book')  # Default priority
            {
                'done': False,
                'title': 'Read book',
                'priority': 'medium'
            }

        Raises:
            ValueError: If priority is invalid

        Logic:
            1. Validate priority (will raise error if invalid)
            2. Create dictionary with all fields
            3. Set done to False (new tasks are incomplete)
            4. Return dictionary
        """
        try:
            validated_priority = self.validate_priority(priority)
        except ValueError as err:
            print(
                '{fail}{error}{reset}'.format(
                    fail=Fore.FAIL,
                    error=str(err),
                    reset=Style.RESET_ALL
                )
            )
            sys.exit(1)

        return {
            'done': False,
            'title': title,
            'priority': validated_priority
        }

    # ============================================================================
    # SEARCH AND FILTER METHODS
    # ============================================================================

    def find_todo_by_index(self, todos, index):
        """
        Finds a todo by its position in the list (1-indexed)

        Users naturally think of lists as 1-indexed (first item is 1, not 0).
        This converts user input to Python's 0-indexed lists.

        Args:
            todos (list): List of todo items
            index (int or str): Position in list (1-indexed)
                               Can be string that converts to int

        Returns:
            dict or None: The todo item, or None if index invalid

        Example:
            >>> todos = [
            ...     {'title': 'Task 1', ...},
            ...     {'title': 'Task 2', ...},
            ...     {'title': 'Task 3', ...}
            ... ]

            >>> find_todo_by_index(todos, 1)
            {'title': 'Task 1', ...}  # First item

            >>> find_todo_by_index(todos, 4)
            None  # Out of range

        Logic:
            1. Convert string to integer if needed
            2. Convert 1-indexed to 0-indexed (subtract 1)
            3. Check if index is within valid range
            4. Return todo if found, None otherwise
        """
        try:
            # Convert to int if string
            list_index = int(index) - 1  # Convert 1-indexed to 0-indexed

            # Check bounds
            if 0 <= list_index < len(todos):
                return todos[list_index]

            return None
        except (ValueError, TypeError):
            return None

    def find_todos_by_title(self, todos, title, exact_match=False):
        """
        Searches for todos matching a title

        Can do exact matching or partial/fuzzy matching.

        Args:
            todos (list): List of todos to search
            title (str): Title to search for
            exact_match (bool): If True, must match exactly
                               If False, partial matches allowed

        Returns:
            list: Todos matching the title

        Example:
            >>> todos = [
            ...     {'title': 'Buy milk'},
            ...     {'title': 'Buy bread'},
            ...     {'title': 'Do laundry'}
            ... ]

            >>> find_todos_by_title(todos, 'Buy', exact_match=False)
            [{'title': 'Buy milk'}, {'title': 'Buy bread'}]

            >>> find_todos_by_title(todos, 'Buy milk', exact_match=True)
            [{'title': 'Buy milk'}]

        Logic:
            1. Iterate through all todos
            2. For each todo, compare title (case-insensitive)
            3. If exact_match: must equal exactly
               Else: title must be contained in todo title
            4. Collect matching todos
            5. Return list of matches
        """
        matches = []
        title_lower = title.lower()

        for todo in todos:
            todo_title_lower = todo['title'].lower()

            if exact_match:
                # Exact matching
                if todo_title_lower == title_lower:
                    matches.append(todo)
            else:
                # Partial matching
                if title_lower in todo_title_lower:
                    matches.append(todo)

        return matches

    def find_todo_index(self, todos, title, exact_match=True):
        """
        Finds the index of a todo by its title

        Args:
            todos (list): List of todos
            title (str): Title to search for
            exact_match (bool): If True, exact match required

        Returns:
            int or None: Index (0-based) or None if not found

        Example:
            >>> find_todo_index(todos, 'Buy milk')
            0  # First item

            >>> find_todo_index(todos, 'Nonexistent')
            None

        Logic:
            1. Iterate through todos with enumeration
            2. Compare each title
            3. Return index of first match
            4. Return None if no match found
        """
        title_lower = title.lower()

        for index, todo in enumerate(todos):
            todo_title_lower = todo['title'].lower()

            if exact_match:
                if todo_title_lower == title_lower:
                    return index
            else:
                if title_lower in todo_title_lower:
                    return index

        return None

    # ============================================================================
    # SORTING METHODS
    # ============================================================================

    def sort_todos_by_priority(self, todos):
        """
        Sorts todos by priority (high first) then by completion status

        High-priority tasks appear first, making them immediately visible.
        Within each priority level, incomplete tasks appear before complete ones.

        Args:
            todos (list): List of todo items

        Returns:
            list: Sorted list (original is not modified)

        Sorting Order:
            1. By priority: high (0) → medium (1) → low (2)
            2. By done status: incomplete (False=0) → complete (True=1)

        Example Input:
            [
                {'title': 'Old task', 'done': True, 'priority': 'high'},
                {'title': 'Urgent fix', 'done': False, 'priority': 'high'},
                {'title': 'Update docs', 'done': False, 'priority': 'medium'},
                {'title': 'Cleanup', 'done': False, 'priority': 'low'}
            ]

        Example Output:
            [
                {'title': 'Urgent fix', 'done': False, 'priority': 'high'},
                {'title': 'Update docs', 'done': False, 'priority': 'medium'},
                {'title': 'Cleanup', 'done': False, 'priority': 'low'},
                {'title': 'Old task', 'done': True, 'priority': 'high'}
            ]

        Logic:
            1. Create priority ranking (high=0, medium=1, low=2)
            2. Define sort key function that returns tuple:
               (is_done, priority_rank)
            3. Use sorted() with key function
            4. Return new sorted list
        """
        # Priority ranking: lower number = higher priority
        priority_rank = {
            'high': 0,
            'medium': 1,
            'low': 2
        }

        def sort_key(todo):
            # Get priority with fallback to default
            priority = todo.get('priority', self.DEFAULT_PRIORITY)
            priority_value = priority_rank.get(priority, 1)

            # Return tuple: (is_done, priority_rank)
            # False (0) comes before True (1), so incomplete tasks first
            return (todo.get('done', False), priority_value)

        return sorted(todos, key=sort_key)

    def sort_todos_by_completion(self, todos):
        """
        Sorts todos by completion status (incomplete first)

        Args:
            todos (list): List of todo items

        Returns:
            list: Sorted list with incomplete tasks first

        Example:
            Input: [
                {'title': 'Task 1', 'done': True},
                {'title': 'Task 2', 'done': False},
                {'title': 'Task 3', 'done': True}
            ]

            Output: [
                {'title': 'Task 2', 'done': False},
                {'title': 'Task 1', 'done': True},
                {'title': 'Task 3', 'done': True}
            ]
        """
        return sorted(todos, key=lambda todo: todo.get('done', False))

    # ============================================================================
    # USER INTERACTION METHODS
    # ============================================================================

    def ask_create_project(self):
        """
        Prompts user to create a new project if none exists

        Called when user tries to use a command but no todos.json exists.

        Output:
            Tells user to run 'todo init' to create a project

        Logic:
            1. Print informative message
            2. Suggest the 'init' command
            3. Exit gracefully
        """
        print(
            '{info}No project found. Create one with: todo init{reset}'.format(
                info=Fore.INFO if hasattr(Fore, 'INFO') else '',
                reset=Style.RESET_ALL
            )
        )
        sys.exit()

    def project_not_found(self):
        """
        Displays error when todos.json doesn't exist

        Similar to ask_create_project but used in different contexts.

        Logic:
            1. Print error message
            2. Suggest solution
            3. Exit
        """
        print(
            '{fail}Error: Project file not found ({file}){reset}'.format(
                fail=Fore.FAIL,
                file=self.PROJECT_FILE,
                reset=Style.RESET_ALL
            )
        )
        print(
            '{info}Create one with: todo init{reset}'.format(
                info=Fore.WARNING,
                reset=Style.RESET_ALL
            )
        )
        sys.exit(1)

    def confirm_action(self, message):
        """
        Asks user for yes/no confirmation

        Used before destructive operations like delete.

        Args:
            message (str): Question to ask user
                          Example: 'Delete this task?'

        Returns:
            bool: True if user entered 'y' or 'yes'
                  False otherwise

        Example:
            >>> if confirm_action('Really delete this?'):
            ...     delete_task()
            ... else:
            ...     print('Cancelled')

        Logic:
            1. Print message with prompt
            2. Get user input
            3. Check if response is 'y' or 'yes' (case-insensitive)
            4. Return boolean
        """
        response = input('{message} (y/n): '.format(message=message))
        return response.lower() in ['y', 'yes']

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    def validate_title(self, title):
        """
        Validates that title is non-empty and reasonable

        Args:
            title (str): Title to validate

        Returns:
            bool: True if valid

        Raises:
            ValueError: If title is invalid
        """
        if not title or not title.strip():
            raise ValueError('Title cannot be empty')

        if len(title.strip()) > 500:
            raise ValueError('Title cannot exceed 500 characters')

        return True

    def validate_todo_item(self, todo):
        """
        Validates that a todo has required fields

        Args:
            todo (dict): Todo item to validate

        Returns:
            bool: True if valid

        Raises:
            ValueError: If todo is missing required fields
        """
        required_fields = ['title', 'done']

        for field in required_fields:
            if field not in todo:
                raise ValueError(
                    'Todo missing required field: {}'.format(field)
                )

        if not isinstance(todo['done'], bool):
            raise ValueError('Field "done" must be boolean')

        # Priority is optional but if present must be valid
        if 'priority' in todo:
            self.validate_priority(todo['priority'])

        return True

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def format_status_message(self, status, message):
        """
        Formats a status message with color coding

        Args:
            status (str): 'success', 'error', 'info', 'warning'
            message (str): Message text

        Returns:
            str: Formatted message with colors

        Example:
            >>> format_status_message('success', 'Task added!')
            '\x1b[92mTask added!\x1b[0m'  # Green colored
        """
        status_colors = {
            'success': Fore.OK,
            'error': Fore.FAIL,
            'info': Fore.INFO if hasattr(Fore, 'INFO') else '',
            'warning': Fore.WARNING
        }

        color = status_colors.get(status, '')
        return '{color}{message}{reset}'.format(
            color=color,
            message=message,
            reset=Style.RESET_ALL
        )

    def print_success(self, message):
        """Prints a success message in green"""
        print(self.format_status_message('success', message))

    def print_error(self, message):
        """Prints an error message in red"""
        print(self.format_status_message('error', message))

    def print_info(self, message):
        """Prints an info message"""
        print(self.format_status_message('info', message))

    def print_warning(self, message):
        """Prints a warning message in yellow"""
        print(self.format_status_message('warning', message))
