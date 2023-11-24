import argparse
from datetime import datetime
import fnmatch
from openai import OpenAI
from typing import Optional

def format_file_size(size_in_bytes: int) -> str:
    """
    Format file size in a human-readable format.

    Args:
    size_in_bytes (int): The file size in bytes.

    Returns:
    str: Human-readable file size.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f}{unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f}PB"

def format_file_output(file_object: "FileObject") -> str:
    """
    Format file details for output in a format similar to 'ls -l'.

    Args:
    file_object (FileObject): The file object containing details to format.

    Returns:
    str: Formatted file details.
    """
    file_size = format_file_size(file_object.bytes)
    created_at = datetime.fromtimestamp(file_object.created_at).strftime("%b %d %Y %H:%M")
    file_name = file_object.filename
    return f"{file_size}\t{created_at}\t{file_name}"

def list_files(client: OpenAI, pattern: str) -> None:
    """
    List files on OpenAI, formatted similar to 'ls -l', matching a specified pattern.

    Args:
    client (OpenAI): The OpenAI client instance.
    pattern (str): The pattern to match filenames against.
    """
    files_list_response = client.files.list()
    total_size = 0
    file_count = 0

    for file_object in files_list_response.data:
        if fnmatch.fnmatch(file_object.filename, pattern):
            print(format_file_output(file_object))
            total_size += file_object.bytes
            file_count += 1

    print(f"\nTotal files: {file_count}")
    print(f"Total size: {format_file_size(total_size)}")

def delete_files(client: OpenAI, pattern: str, dry_run: bool = False, confirm_deletion: bool = True) -> None:
    """
    Delete files from OpenAI matching a specified pattern, with options for dry run and confirmation.
    Track and summarize deleted files and their total size, including dry run statistics.

    Args:
    client (OpenAI): The OpenAI client instance.
    pattern (str): The pattern to match filenames against.
    dry_run (bool): If True, only simulate deletion. Default: False.
    confirm_deletion (bool): If True, prompt for confirmation before deletion. Default: True.

    In dry run mode, the function prints the number of files and the total size of files
    that would be deleted. In actual deletion mode, it shows the count and size of files
    successfully deleted.
    """
    files_list_response = client.files.list()
    total_size_dry_run = 0
    files_count_dry_run = 0
    total_deleted_size = 0
    deleted_files = 0

    for file_object in files_list_response.data:
        if fnmatch.fnmatch(file_object.filename, pattern):
            formatted_output = format_file_output(file_object)
            file_size = file_object.bytes  # Capture file size for dry run and actual deletion

            if dry_run:
                print(f"[DRY RUN] Deleted: {formatted_output}")
                total_size_dry_run += file_size
                files_count_dry_run += 1
            else:
                if confirm_deletion:
                    response = input(f"Are you sure you want to delete {formatted_output}? [y/N]: ")
                    if response.lower() != 'y':
                        continue
                delete_response = client.files.delete(file_object.id)
                if getattr(delete_response, 'deleted', False):
                    print(f"Deleted: {formatted_output}")
                    total_deleted_size += file_size
                    deleted_files += 1
                else:
                    print(f"Failed to delete file: {formatted_output}")

    if dry_run:
        print(f"\nNO files deleted. Would have deleted {files_count_dry_run} files totaling {format_file_size(total_size_dry_run)} without '--dry-run'.")
    elif not dry_run:
        print(f"\nDeleted {deleted_files} files totaling {format_file_size(total_deleted_size)}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage files on OpenAI. If you pass a file pattern, surround the pattern with quotes, for example: --delete '*.py'",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--dry-run", action="store_true", help="Only list the files that would be deleted, without actually deleting them.")
    parser.add_argument("-l", "--list", nargs="?", const="*", default=None, help="List files matching a given pattern (default: '*').\nNOTE: Surround file pattern with quotes, e.g., --list '*.py'.")
    parser.add_argument("-d", "--delete", nargs="+", help="Delete files matching a given pattern.\nNOTE: Surround file pattern with quotes, e.g., --delete '*.py'.")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatic yes to prompts; assume 'yes' as answer to all prompts and run non-interactively.")

    args = parser.parse_args()
    client = OpenAI()

    if args.list is not None:
        list_files(client, args.list)
    elif args.delete:
        pattern = " ".join(args.delete)
        delete_files(client, pattern, args.dry_run, not args.yes)
    else:
        # Display help message if no arguments are provided
        parser.print_help()
