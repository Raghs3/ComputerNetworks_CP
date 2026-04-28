"""
Non-interactive wrapper for NetworkMonitor.
Usage: python run_monitor.py <target> <csv_path>
"""
import sys
from network_monitor import NetworkMonitor

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_monitor.py <target> <csv_path>")
        sys.exit(1)

    target = sys.argv[1]
    if target.startswith("http://"):
        target = target[7:]
    elif target.startswith("https://"):
        target = target[8:]
    target = target.rstrip("/")
    csv_path = sys.argv[2]
    monitor = NetworkMonitor(target=target, csv_filename=csv_path)
    monitor.run()
