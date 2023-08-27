import glob
import os
import hashlib
import json
from typing import List
import multiprocessing

# Config
NUM_CPU_CORES = 8

# START_FOLDER = "test-folder"
HASH_FILE = "hashes.json"
DUPLICATES_FILE = "duplicates.json"


# Compute MD5 function copied from https://debugpointer.com/python/create-md5-hash-of-a-file-in-python
def compute_md5(file_path: str):
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def hash_file_paths(cpu_index: int, file_paths: List):
    print(f"{cpu_index}: Generating hashes for {len(file_paths)} files...", flush=True)
    
    hashes = {}
    for index, file_path in enumerate(file_paths):
        if index % 1000 == 0:
            print(f"{cpu_index}: Generating hash for file {index}/{len(file_paths)}")

        hashes[file_path] = compute_md5(file_path)

    with open(f"hashes-{cpu_index}.json", "w") as f:
        f.write(json.dumps(hashes, indent=2))

def format_size(num_bytes):
    size_suffix = ["B", "KB", "MB", "GB", "TB", "PB"]

    divisions = 0
    shrunk_bytes = num_bytes
    while shrunk_bytes > 0:
        if shrunk_bytes // 1000 > 0:
            shrunk_bytes = shrunk_bytes // 1000
            divisions += 1
        else:
            break

    return f"{shrunk_bytes} {size_suffix[divisions]}"



if __name__ == "__main__":

    # Get all of the file paths
    print("Getting all file paths...")
    all_paths = glob.glob(f"{START_FOLDER}/**", recursive=True)
    file_paths = [all_path for all_path in all_paths if not os.path.isdir(all_path)]
    print(f"There are {len(file_paths):,} files")

    # Get file sizes
    print("Splitting file paths among threads...")
    split_file_paths = {i: [] for i in range(NUM_CPU_CORES)}
    split_file_sizes = {i: 0 for i in range(NUM_CPU_CORES)}
    for index, file_path in enumerate(file_paths):
        if index % 10_000 == 0:
            print(f"Getting size for file {index}/{len(file_paths)}")
        
        size = os.path.getsize(file_path)
        min_cpu_index = min(split_file_sizes, key=split_file_sizes.get)

        split_file_paths[min_cpu_index].append(file_path)
        split_file_sizes[min_cpu_index] += size

    # Generating the md5 hashes
    processes = []
    for index, cpu_file_paths in split_file_paths.items():
        process = multiprocessing.Process(target=hash_file_paths, args=(index, cpu_file_paths,))
        processes.append(process)
        process.start()
    
    for process in processes:
        process.join()

    # Combining the results from the cpus
    hashes = {}
    for i in range(NUM_CPU_CORES):
        hash_dict = {}
        with open(f"hashes-{i}.json", "r") as f:
            hash_dict = json.loads(f.read())
            hashes.update(hash_dict)

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
    
    print(f"You have a total of {total_duplicated_files:,} duplicated files which is wasting {format_size(total_size_duplicated)} worth of space.")
