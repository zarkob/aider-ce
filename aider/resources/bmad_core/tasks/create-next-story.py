import os
import sys

def create_next_story_prompt():
    shards_dir = ".bmad/shards"

    # Read the content of all shards
    shards_content = ""
    for shard_filename in sorted(os.listdir(shards_dir)):
        with open(os.path.join(shards_dir, shard_filename), 'r') as shard_file:
            shards_content += shard_file.read()

    prompt = f"""
Based on the following planning documents, please generate the next logical user story.

The user story should be in markdown format and include:
- A clear and concise title.
- A user story description in the format: "As a [user type], I want [an action] so that [a benefit]."
- A list of acceptance criteria that define the conditions for the story to be considered complete.
- Any relevant technical notes or references to the planning documents.

Here are the planning documents:

{shards_content}
"""

    print(prompt)

if __name__ == "__main__":
    create_next_story_prompt()
