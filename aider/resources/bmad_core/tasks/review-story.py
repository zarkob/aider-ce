import os
import sys

def review_story_prompt(story_path, code_changes):
    with open(story_path, 'r') as story_file:
        story_content = story_file.read()

    prompt = f"""
Based on the following user story and code changes, please review the code and provide feedback.

Your feedback should indicate whether you approve or reject the code changes, and it should provide a detailed explanation for your decision.

Here is the user story:

{story_content}

Here are the code changes:

{code_changes}
"""

    print(prompt)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python review-story.py <path_to_story_file> \"<code_changes>\"")
        sys.exit(1)

    review_story_prompt(sys.argv[1], sys.argv[2])
