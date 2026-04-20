"""
Quick test script to verify website monitoring functionality
This bypasses the interactive input for testing purposes
"""

from network_monitor import NetworkMonitor

# Test with a specific website
print("\n🧪 Testing Network Monitor with google.com...")
print("="*60)

# Create monitor instance with google.com
monitor = NetworkMonitor(
    target="google.com",
    window_size=10,  # Use smaller window for quick testing
    csv_filename="test_google_com.csv"
)

# Run for 10 seconds only (10 pings)
print("\n▶ Monitoring for 10 seconds...\n")
monitor.run(duration=10)

print("\n✅ Test completed! Check test_google_com.csv for results.")
