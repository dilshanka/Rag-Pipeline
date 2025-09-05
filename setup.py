#!/usr/bin/env python3
"""
Setup script for Academic Study Assistant
This script helps students set up the RAG system quickly.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("🎓 Academic Study Assistant Setup")
    print("=" * 40)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please check your internet connection and try again.")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    # Create university_documents directory
    docs_dir = Path("university_documents")
    docs_dir.mkdir(exist_ok=True)
    print(f"✅ Created {docs_dir}")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write("# Academic Study Assistant Configuration\n")
            f.write("OPENAI_API_KEY=your_api_key_here\n")
            f.write("OPENAI_OCR_MODEL=gpt-4o-mini\n")
            f.write("OCR_DPI=220\n")
        print("✅ Created .env file (please add your OpenAI API key)")
    else:
        print("✅ .env file already exists")

def check_openai_key():
    """Check if OpenAI API key is configured"""
    print("\n🔑 Checking OpenAI API key...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your_api_key_here":
            print("✅ OpenAI API key is configured")
            return True
        else:
            print("⚠️  OpenAI API key not configured")
            print("   Please edit .env file and add your OpenAI API key")
            return False
    except ImportError:
        print("⚠️  python-dotenv not installed yet")
        return False

def show_next_steps():
    """Show next steps to the user"""
    print("\n🚀 Setup Complete! Next Steps:")
    print("=" * 40)
    print("1. Add your course materials to the 'university_documents' folder")
    print("2. Edit .env file and add your OpenAI API key")
    print("3. Process your documents:")
    print("   python chromadbpdf.py")
    print("4. Start the study assistant:")
    print("   python rag_api.py")
    print("5. Open student_interface.html in your browser")
    print("\n📚 Example questions to try:")
    print("   - 'What are the main concepts in this chapter?'")
    print("   - 'Can you explain this topic in simpler terms?'")
    print("   - 'What should I focus on for the exam?'")

def main():
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Install requirements
    install_requirements()
    
    # Create directories and files
    create_directories()
    
    # Check OpenAI key
    has_api_key = check_openai_key()
    
    # Show next steps
    show_next_steps()
    
    if not has_api_key:
        print("\n⚠️  Remember to add your OpenAI API key to the .env file before processing documents!")

if __name__ == "__main__":
    main()
