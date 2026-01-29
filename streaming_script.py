# This script runs the data simulator directly
# The data_simulator.py file contains the main loop
# Just run: python data_simulator.py

import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Starting fraud transaction generator...")
    print("💡 This will generate transactions with ~30% fraud rate")
    print("📊 Watch the dashboard to see fraud transactions appear in real-time!")
    print("=" * 60)
    # Run the data simulator
    subprocess.run([sys.executable, "data_simulator.py"])