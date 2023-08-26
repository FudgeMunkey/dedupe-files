import glob
import os
import hashlib
import json

START_FOLDER = "/Users/alexh/Downloads"
HASH_FILE = "hashes.json"
DUPLICATES_FILE = "duplicates.json"

# Compute MD5 function copied from https://debugpointer.com/python/create-md5-hash-of-a-file-in-python
def compute_md5(file_path: str):
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()

if __name__ == "__main__":
    # Get all of the file paths
    print("Getting all file paths...")
    all_paths = glob.glob(f"{START_FOLDER}/**", recursive=True)
    file_paths = [all_path for all_path in all_paths if not os.path.isdir(all_path)]
    print(f"There are {len(file_paths)} files")

    # Generate hashes for each of the files
    print("Generating hashes for all files...")
    hashes = {}
    for index, file_path in enumerate(file_paths):
        if index % 1000 == 0:
            print(f"Generating hash for file {index}/{len(file_paths)}")

        hashes[file_path] = compute_md5(file_path)

        with open(HASH_FILE, "w") as f:
            f.write(json.dumps(hashes, indent=2))

    # Inverse the hashes to find the duplicates
    print("Finding duplicates...")
    duplicates = {}
    for file_path, hash in hashes.items():
        if hash not in duplicates:
            duplicates[hash] = [file_path]
        else:
            duplicates[hash].append(file_path)
    
    # Remove non duplicate hashes
    for hash in list(duplicates.keys()):
        if len(duplicates[hash]) == 1:
            del duplicates[hash]

    with open(DUPLICATES_FILE, "w") as f:
        f.write(json.dumps(duplicates, indent=2))

    # Calculate space wasted by duplicates
    print("Generating statistics...")
    total_duplicated_files = 0
    total_size_duplicated = 0
    for hash, file_paths in duplicates.items():
        duplicated_files = len(file_paths) - 1
        total_duplicated_files += duplicated_files
        total_size_duplicated += os.path.getsize(file_paths[0]) * duplicated_files
    
    print(f"You have a total of {total_duplicated_files} duplicated files which is wasting {total_size_duplicated} B worth of space.")
