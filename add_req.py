import subprocess

def add_requirements(requirements_file):
    with open(requirements_file, 'r') as file:
        for line in file:
            package = line.strip()
            if package and not package.startswith('#'):
                subprocess.run(['poetry', 'add', package])

if __name__ == "__main__":
    add_requirements('requirements.txt')