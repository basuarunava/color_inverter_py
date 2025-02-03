# List of required packages for the PDF Color Inverter app
requirements = [
    "gradio",
    "PyMuPDF",
    "numpy"
]

def print_requirements():
    for pkg in requirements:
        print(pkg)

if __name__ == "__main__":
    print("Required packages:")
    print_requirements()