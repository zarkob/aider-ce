import os
import sys

def develop_story_prompt(story_path):
    with open(story_path, 'r') as story_file:
        story_content = story_file.read()

    prompt = f"""
Based on the following user story, please generate the necessary code changes to implement it.

The code changes should be in Aider's `editblock` format.

Here is the user story:

{story_content}
"""

    print(prompt)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python develop-story.py <path_to_story_file>")
        sys.exit(1)

    develop_story_prompt(sys.argv[1])
