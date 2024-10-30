import os
import subprocess
import glob
import shlex

# Directory containing your HTML, CSS, and JavaScript files
project_dir = '.'

def format_files():
    # Glob pattern to match files
    patterns = ['**/*.html', '**/*.css', '**/*.js', '**/*.json', '**/*.md']
    
    # List to hold all matched files
    files_to_format = []

    # Expand the glob patterns
    for pattern in patterns:
        files_to_format.extend(glob.glob(os.path.join(project_dir, pattern), recursive=True))

    # Command to run Prettier
    prettier_command = ['prettier', '--write'] + files_to_format

    # Run the Prettier command
    subprocess.run(prettier_command, shell=False)

if __name__ == "__main__":
    format_files()