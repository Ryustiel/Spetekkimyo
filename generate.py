import sys
from spetekkimyo import generate_font

def main():
    if len(sys.argv) != 2:
        print("Usage: python file.py <output_path>")
        sys.exit(1)

    output_path = sys.argv[1]

    try:
        generate_font(output_path)
        print(f"Font successfully generated at: {output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()