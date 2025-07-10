import streamlit as st
import os
import sys

# Add the current directory to Python path to import shared modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the client chat interface
from client_chat_interface import main

if __name__ == "__main__":
    main() 