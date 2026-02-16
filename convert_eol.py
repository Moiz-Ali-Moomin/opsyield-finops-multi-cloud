import os

def convert_to_lf(directory):
    extensions = {'.py', '.js', '.ts', '.tsx', '.css', '.html', '.json', '.md'}
    for root, dirs, files in os.walk(directory):
        if '.git' in root or 'node_modules' in root or '__pycache__' in root or 'build' in root:
            continue
        for f in files:
            if os.path.splitext(f)[1] in extensions:
                path = os.path.join(root, f)
                try:
                    with open(path, 'rb') as f_in:
                        content = f_in.read()
                    if b'\r\n' in content:
                        print(f"Converting {path}")
                        with open(path, 'wb') as f_out:
                            f_out.write(content.replace(b'\r\n', b'\n'))
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    convert_to_lf('.')
