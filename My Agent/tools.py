import os
from typing import Optional, List


def get_all_drives() -> List[str]:
    """Get all available drives on Windows"""
    drives = []
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f"{letter}:/"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def search_files(query: str, directory: str = "all", max_results: int = 10, file_type: str = "all") -> str:
    """
    Search for files matching the query in common user folders (FAST version)
    """

    # File type categories
    FILE_TYPES = {
        "audio": ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.aiff'],
        "video": ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp'],
        "image": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico', '.psd', '.raw'],
        "document": ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
        "code": ['.py', '.java', '.cpp', '.c', '.js', '.html', '.css', '.php', '.rb', '.go', '.rs', '.sql', '.json',
                 '.xml'],
        "archive": ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
        "executable": ['.exe', '.msi', '.bat', '.sh', '.app', '.apk', '.jar'],
        "all": []
    }

    matches = []
    search_query = query.lower()

    # Get file extensions to filter
    if file_type.lower() in FILE_TYPES:
        extensions = FILE_TYPES[file_type.lower()]
    else:
        extensions = []

    # Search only common user folders for better performance
    user_home = os.path.expanduser("~")
    common_folders = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Music"),
        os.path.join(user_home, "Videos"),
        os.path.join(user_home, "Pictures"),
        "E:/",  # Search entire E: drive
    ]

    # Add E: drive if it exists
    if os.path.exists("E:/"):
        common_folders.append("E:/")

    print(f"Searching in user folders for '{query}'...")
    if file_type != "all":
        print(f"Filtering for: {file_type} files")

    # Search in each directory
    for search_dir in common_folders:
        if not os.path.exists(search_dir):
            continue

        try:
            # Limit depth to avoid searching too deep
            for root, dirs, files in os.walk(search_dir):
                # Skip hidden and system folders
                if '$RECYCLE.BIN' in root.upper() or 'APPDATA' in root.upper():
                    continue

                # Limit depth - only go 3 levels deep
                depth = root.replace(search_dir, '').count(os.sep)
                if depth > 3:
                    dirs[:] = []  # Don't go deeper
                    continue

                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    'node_modules', '.git', '__pycache__', '.venv', 'venv'
                ]]

                for file in files:
                    # Check if filename matches query
                    if search_query in file.lower():
                        # Check file type filter
                        if file_type == "all" or any(file.lower().endswith(ext) for ext in extensions):
                            full_path = os.path.join(root, file)
                            try:
                                file_size = os.path.getsize(full_path) / (1024 * 1024)  # MB
                                matches.append((full_path, file_size))

                                if len(matches) >= max_results:
                                    break
                            except:
                                continue

                if len(matches) >= max_results:
                    break

        except PermissionError:
            continue
        except Exception as e:
            continue

        if len(matches) >= max_results:
            break

    if matches:
        result = f"Found {len(matches)} file(s):\n\n"
        for i, (path, size) in enumerate(matches):
            result += f"{i + 1}. {path} ({size:.2f} MB)\n"
        return result
    else:
        return f"No files found matching '{query}' in common folders"


# Test
if __name__ == "__main__":
    print("Available drives:", get_all_drives())
    print("\n" + "=" * 60 + "\n")

    result = search_files("music", max_results=5, file_type="audio")
    print(result)
