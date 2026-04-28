"""
Quick Test Script - Run for 30 seconds to verify the system
"""

from network_monitor import NetworkMonitor

if __name__ == "__main__":
    print("\n🧪 Testing Network Monitor for 30 seconds...\n")
    
    # Create monitor with test configuration
    monitor = NetworkMonitor(
        target="8.8.8.8",
        window_size=10,  # Smaller window for quick test
        csv_filename="data/test_network_data.csv"
    )
    
    # Run for 30 seconds
    monitor.run(duration=30)
    
    print("\n Test completed! Check 'data/test_network_data.csv' for results.")
