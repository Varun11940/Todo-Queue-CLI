from __future__ import absolute_import

import re
import sys
import json

from todo.commands.base import Command
from todo.utils.styles import Fore, Style


class PrioCommand(Command):
    """
    Command to change priority of existing tasks

    Usage Examples:
        todo prio 1 high          # Change task #1 to high priority
        todo prio "Buy milk" low  # Change task named "Buy milk" to low priority
        todo prio 2 medium        # Change task #2 to medium priority
    """

    def parse_prio_input(self):
        """
        Parses command input to extract task identifier and new priority

        Returns:
            tuple: (task_identifier, priority) where task_identifier can be:
                   - Index number (string like "1", "2")
                   - Task title (string like "Buy milk")

        Example:
            Input: "todo prio 1 high"
            → get_command_attributes() returns "1 high"
            → parse_prio_input() returns ("1", "high")

            Input: "todo prio 'Buy milk' medium"
            → get_command_attributes() returns "'Buy milk' medium"
            → parse_prio_input() returns ("Buy milk", "medium")

        Logic:
            1. Get all attributes after command name
            2. Check if we have input
            3. Split from the right to get last word as priority
            4. Everything else is the task identifier
            5. Validate we have both parts
            6. Return as tuple
        """
        attributes = self.get_command_attributes()

        if not attributes:
            print(
                '{fail}Usage: todo prio <task_number_or_title> <priority>{reset}'.format(
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL,
                )
            )
            sys.exit(1)

        # Split from right, max 1 split to separate priority from identifier
        # Example: "1 high" → ["1", "high"]
        # Example: "Buy milk high" → ["Buy milk", "high"]
        parts = attributes.rsplit(' ', 1)

        if len(parts) != 2:
            print(
                '{fail}Error: Please provide both task identifier and priority{reset}'.format(
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL,
                )
            )
            sys.exit(1)

        task_id, priority = parts
        return task_id.strip(), priority.strip()

    def find_todo_by_identifier(self, todos, identifier):
        """
        Finds a todo by either index number or title

        Args:
            todos (list): List of all todos
            identifier (str): Either a number (1-indexed) or task title

        Returns:
            tuple: (index_in_list, todo_item) or (None, None) if not found

        Example:
            # Search by index
            identifier = "1"
            → find_todo_by_identifier(todos, "1")
            → (0, {"title": "Buy milk", ...})  # Returns 0-indexed position

            # Search by title
            identifier = "Buy milk"
            → find_todo_by_identifier(todos, "Buy milk")
            → (0, {"title": "Buy milk", ...})

        Logic:
            1. Try to convert identifier to integer (1-indexed)
            2. If conversion succeeds, search by index
            3. If conversion fails, search by title
            4. Return (index, todo) tuple or (None, None)
        """
        # Try to parse as index number first
        try:
            # Convert to integer, then to 0-indexed
            list_index = int(identifier) - 1

            # Check if index is valid
            if 0 <= list_index < len(todos):
                return list_index, todos[list_index]

            # Index out of range
            return None, None

        except ValueError:
            # Not a number, search by title
            identifier_lower = identifier.lower()

            for index, todo in enumerate(todos):
                if todo['title'].lower() == identifier_lower:
                    return index, todo

            return None, None

    def update_todo_priority(self, todo, new_priority):
        """
        Updates a todo's priority field

        Args:
            todo (dict): Todo item to update
            new_priority (str): New priority level (low, medium, high)

        Returns:
            dict: Updated todo with new priority

        Example:
            Before: {"done": false, "title": "Buy milk", "priority": "low"}
            After:  {"done": false, "title": "Buy milk", "priority": "high"}

        Logic:
            1. Create copy of todo (don't modify original)
            2. Validate the new priority
            3. Update priority field
            4. Return updated copy
        """
        updated_todo = todo.copy()

        try:
            # Validate priority (will raise error if invalid)
            validated_priority = self.validate_priority(new_priority)
        except ValueError as err:
            print(
                '{fail}{error}{reset}'.format(
                    fail=Fore.FAIL,
                    error=str(err),
                    reset=Style.RESET_ALL,
                )
            )
            sys.exit(1)

        updated_todo['priority'] = validated_priority
        return updated_todo

    def run(self):
        """
        Main execution when user types 'todo prio ...'

        Flow:
            1. Read todos.json
            2. Parse user input (task identifier and new priority)
            3. Find todo by index or title
            4. Validate priority
            5. Update priority field
            6. Save updated list to todos.json
            7. Print confirmation message

        Example Execution:
            Command: todo prio 2 high

            Step 1: Read todos.json with current tasks
            Step 2: Parse → task_id="2", priority="high"
            Step 3: Find todo at index 2
            Step 4: Validate "high" is valid priority
            Step 5: Update that todo's priority to "high"
            Step 6: Save updated todos.json
            Step 7: Print "Priority changed!"


        Example Execution 2:
            Command: todo prio "Buy milk" low

            Step 1: Read todos.json
            Step 2: Parse → task_id="Buy milk", priority="low"
            Step 3: Find todo with title "Buy milk"
            Step 4-7: Same as above
        """

        # Step 1: Read todos.json
        try:
            with open(self.PROJECT_FILE, 'r') as project_file:
                data = json.load(project_file)
        except FileNotFoundError:
            self.project_not_found()
            return
        except:
            print(
                '{fail}Error reading project file{reset}'.format(
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL,
                )
            )
            sys.exit(1)

        # Extract project info
        try:
            name = data['name']
        except:
            name = self.UNTITLED_NAME

        try:
            todos = data['todos']
        except:
            todos = []

        # Step 2: Parse input
        task_id, new_priority = self.parse_prio_input()

        # Step 3: Find the todo
        list_index, todo = self.find_todo_by_identifier(todos, task_id)

        if todo is None:
            print(
                '{fail}Task not found: {target}{reset}'.format(
                    target=task_id,
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL,
                )
            )
            sys.exit(1)

        # Step 4-5: Validate and update priority
        old_priority = todo.get('priority', self.DEFAULT_PRIORITY)
        updated_todo = self.update_todo_priority(todo, new_priority)
        todos[list_index] = updated_todo

        # Step 6: Save to file
        new_data = {
            'name': name,
            'todos': todos
        }
        self.update_project(new_data)

        # Step 7: Print confirmation
        print(
            '{ok}✓ Priority changed: {title}{reset} ({old} → {new})'.format(
                ok=Fore.GREEN,
                title=todo['title'],
                old=old_priority.upper(),
                new=new_priority.upper(),
                reset=Style.RESET_ALL,
            )
        )


Prio = PrioCommand()
