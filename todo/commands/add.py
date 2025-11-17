from __future__ import absolute_import

import os
import sys
import json
import re

from todo.commands.base import Command
from todo.utils.styles import Fore, Style


class AddCommand(Command):
    def parse_priority_from_input(self, input_string):
        """
        Extracts priority flag from user input

        Args:
            input_string (str): Raw user input

        Returns:
            tuple: (title_without_flag, priority)

        Example:
            Input: "Buy milk --priority=high"
            Output: ("Buy milk", "high")

            Input: "Do laundry"
            Output: ("Do laundry", "medium")  # default

        Logic:
            1. Use regex to find --priority=value pattern (case-insensitive)
            2. Extract the priority value after equals sign
            3. Remove the entire flag from the title
            4. If no flag found, use default priority
            5. Return (cleaned_title, priority) tuple
        """
        # Regex pattern: matches "--priority=" followed by word characters
        # Example matches: --priority=high, --priority=MEDIUM, --priority=low
        priority_pattern = r'--priority=(\w+)'

        # Search for the pattern (case-insensitive flag)
        match = re.search(priority_pattern, input_string, re.IGNORECASE)

        if match:
            # Found a priority flag
            # match.group(1) = the value after --priority=
            priority = match.group(1).lower()

            # Remove the --priority=X flag from input to get clean title
            # re.sub replaces all occurrences of pattern with empty string
            title = re.sub(priority_pattern, '', input_string,
                           flags=re.IGNORECASE).strip()

            return title, priority

        # No priority flag found, use default
        return input_string.strip(), self.DEFAULT_PRIORITY

    def update_todos(self, todos=[]):
        """
        Creates a copy of the todo list with new items

        Now supports parsing priority from input

        Example:
            Input titles:
            - "Buy milk --priority=high"
            - "Do laundry"

            Output:
            [
                {"done": false, "title": "Buy milk", "priority": "high"},
                {"done": false, "title": "Do laundry", "priority": "medium"}
            ]
        """
        new_todos = todos.copy()

        for item in self.get_titles_input():
            # Parse title and priority from input
            title, priority = self.parse_priority_from_input(item)

            # Create todo with priority field
            new_item = {
                "done": False,
                "title": title,
                "priority": priority
            }
            new_todos.append(new_item)

        return new_todos

    def run(self):
        try:
            with open(self.PROJECT_FILE, 'r') as project_file:
                data = json.load(project_file)
        except FileNotFoundError:
            self.ask_create_project()
            self.run()
            return
        except:
            print(
                '{fail}An error has occured while adding todos.{reset}'
                .format(
                    fail=Fore.FAIL,
                    reset=Style.RESET_ALL,
                )
            )
            sys.exit(1)

        try:
            name = data['name']
        except:
            name = self.UNTITLED_NAME

        try:
            todos = data['todos']
        except:
            todos = []

        new_data = {
            'name': name,
            'todos': self.update_todos(todos)
        }

        self.update_project(new_data)

        print(
            '{ok}✓ Task(s) added successfully!{reset}'
            .format(
                ok=Fore.GREEN,
                reset=Style.RESET_ALL,
            )
        )


Add = AddCommand()
