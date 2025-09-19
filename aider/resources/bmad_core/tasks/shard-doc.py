import re
import sys
import os

def shard_document(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Split the document by headers (lines starting with #, ##, ###, etc.)
    shards = re.split(r'(^#+\s.*)', content, flags=re.MULTILINE)

    shards_dir = ".bmad/shards"
    os.makedirs(shards_dir, exist_ok=True)

    # Clean the shards directory
    for f in os.listdir(shards_dir):
        os.remove(os.path.join(shards_dir, f))

    # The first element of the split is usually empty, so we skip it.
    # Then, we iterate over the shards in pairs (header, content)
    shard_num = 0
    for i in range(1, len(shards), 2):
        header = shards[i]
        body = shards[i+1]

        # Create a valid filename from the header
        shard_filename = f"shard-{shard_num}.md"
        shard_num += 1

        with open(os.path.join(shards_dir, shard_filename), 'w') as shard_file:
            shard_file.write(header + body)

    print(f"Sharding complete. {shard_num} shards created in {shards_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python shard-doc.py <path_to_markdown_file>")
        sys.exit(1)

    shard_document(sys.argv[1])
