import os

# Available only IS_DEBUG is False

for root, dirs, files in os.walk("test_data"):
    for file in files:
        # skip the bonus test cases
        if file.startswith("b"):
            break
        # copy current file to input.txt
        with open(os.path.join(root, file), "r") as f:
            with open("input.txt", "w") as f2:
                f2.write(f.read())
        # run main.py
        print("Running main.py with input file: " + file)
        os.system("python main.py")
