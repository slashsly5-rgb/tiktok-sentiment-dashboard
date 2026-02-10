import streamlit as st
import sys
import os

# Add backend to path so imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Path to the actual application file
app_path = os.path.join(backend_dir, "app.py")

# execute the application file
with open(app_path) as f:
    exec(f.read())
