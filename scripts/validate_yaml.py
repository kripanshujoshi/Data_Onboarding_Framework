import yaml
import sys
import os

try:
    with open(sys.argv[1], 'r') as file:
        yaml.safe_load(file)
    print("YAML file is valid!")
except yaml.YAMLError as e:
    print(f"Error in YAML file: {e}")
except Exception as e:
    print(f"Error: {e}")
