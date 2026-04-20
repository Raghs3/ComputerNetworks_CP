# -*- coding: utf-8 -*-
"""
Real-Time Network Quality Prediction System
Phase 1: Data Collection and Feature Extraction

This script:
1. Automation pings to collect RTT every second
2. Calculates network metrics (Jitter, Loss, Throughput)
3. Computes moving averages
4. Normalizes features
5. Stores all data in CSV
"""

import subprocess
import re
import time
import csv
import os
import socket
from datetime import datetime
from collections import deque
import statistics


class NetworkMonitor:
    def __init__(self, target="8.8.8.8", window_size=20, csv_filename="network_data.csv"):
        """
        Initialize the Network Monitor
        
        Args:
            target: IP address or hostname to ping (default: Google DNS)
            window_size: Number of recent samples to keep for calculations
            csv_filename: Name of the CSV file to store data
        """
        self.target = target
        self.window_size = window_size
        self.csv_filename = csv_filename
        
        # Sliding windows to store recent values
        self.rtt_window = deque(maxlen=window_size)
        self.jitter_window = deque(maxlen=window_size)
        self.loss_window = deque(maxlen=window_size)
        
        # Tracking variables
        self.previous_rtt = None
        self.total_pings = 0
        self.failed_pings = 0
        self.resolved_ip = None
        
        # Resolve hostname to IP
        self._resolve_target()
        
        # Initialize CSV file
        self._initialize_csv()
    
    def _resolve_target(self):
        """Resolve hostname to IP address"""
        try:
            self.resolved_ip = socket.gethostbyname(self.target)
            print(f" DNS Resolved: {self.target} -> {self.resolved_ip}")
        except socket.gaierror:
            print(f" WARNING: Could not resolve {self.target}")
            print(f" Will still attempt to ping...")
            self.resolved_ip = self.target
        
    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist"""
        file_exists = os.path.isfile(self.csv_filename)
        
        if not file_exists:
            with open(self.csv_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Timestamp',
                    'RTT (ms)',
                    'Jitter (ms)',
                    'Packet Loss (%)',
                    'Throughput (Kbps)',
                    'Moving Avg RTT',
                    'Moving Avg Jitter',
                    'Moving Avg Loss',
                    'Normalized RTT',
                    'Normalized Jitter',
                    'Normalized Loss',
                    'Normalized Throughput'
                ])
            print(f" Created CSV file: {self.csv_filename}")
    
    def ping_once(self):
        """
        Execute a single ping and extract RTT
        
        Returns:
            float: RTT in milliseconds, or None if ping failed
        """
        try:
            # Windows ping command: ping -n 1 (send 1 packet)
            result = subprocess.run(
                ['ping', '-n', '1', self.target],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse RTT from output using regex
            # Example output: "Reply from 8.8.8.8: bytes=32 time=23ms TTL=116"
            match = re.search(r'time[=<](\d+)ms', result.stdout)
            
            if match:
                rtt = float(match.group(1))
                # Extract the IP from the reply for verification
                ip_match = re.search(r'Reply from ([\d\.]+):', result.stdout)
                if ip_match and self.total_pings == 0:
                    print(f" First ping successful! Reply from: {ip_match.group(1)}")
                return rtt
            else:
                # Check if ping failed
                if 'Request timed out' in result.stdout:
                    if self.total_pings % 10 == 0:  # Print every 10th failure
                        print(f" Ping timeout to {self.target}")
                elif 'could not find host' in result.stdout.lower():
                    print(f" ERROR: Could not find host {self.target}")
                return None
                
        except (subprocess.TimeoutExpired, Exception) as e:
            if self.total_pings % 10 == 0:  # Print every 10th error
                print(f" WARNING: Ping failed: {e}")
            return None
    
    def calculate_jitter(self, current_rtt):
        """
        Calculate jitter (variation in delay between consecutive packets)
        
        Args:
            current_rtt: Current RTT value
            
        Returns:
            float: Jitter in milliseconds
        """
        if self.previous_rtt is None:
            jitter = 0.0
        else:
            # Jitter = absolute difference between consecutive RTTs
            jitter = abs(current_rtt - self.previous_rtt)
        
        self.previous_rtt = current_rtt
        return jitter
    
    def calculate_packet_loss(self):
        """
        Calculate packet loss percentage
        
        Returns:
            float: Packet loss percentage (0-100)
        """
        if self.total_pings == 0:
            return 0.0
        
        loss_percentage = (self.failed_pings / self.total_pings) * 100
        return loss_percentage
    
    def estimate_throughput(self, rtt):
        """
        Estimate throughput based on RTT
        Formula: Throughput ≈ (Packet Size / RTT)
        
        Assumptions:
        - Packet size: 32 bytes (standard ping packet)
        - Simple inverse relationship: lower RTT = higher throughput
        
        Args:
            rtt: Round-trip time in milliseconds
            
        Returns:
            float: Estimated throughput in Kbps
        """
        if rtt == 0 or rtt is None:
            return 0.0
        
        packet_size_bits = 32 * 8  # 32 bytes = 256 bits
        rtt_seconds = rtt / 1000.0  # Convert ms to seconds
        
        # Throughput in bps, convert to Kbps
        throughput_kbps = (packet_size_bits / rtt_seconds) / 1000
        
        return round(throughput_kbps, 2)
    
    def calculate_moving_average(self, window):
        """
        Calculate moving average of values in a window
        
        Args:
            window: deque containing recent values
            
        Returns:
            float: Moving average
        """
        if len(window) == 0:
            return 0.0
        
        return statistics.mean(window)
    
    def normalize_value(self, value, min_val, max_val):
        """
        Normalize value to 0-1 range using min-max normalization
        
        Args:
            value: Value to normalize
            min_val: Minimum value in the range
            max_val: Maximum value in the range
            
        Returns:
            float: Normalized value (0-1)
        """
        if max_val == min_val:
            return 0.5  # Avoid division by zero
        
        normalized = (value - min_val) / (max_val - min_val)
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, normalized))
    
    def normalize_features(self, rtt, jitter, loss, throughput):
        """
        Normalize all features to 0-1 scale
        
        Expected ranges (adjust based on your network):
        - RTT: 0-200 ms (typical range)
        - Jitter: 0-100 ms
        - Packet Loss: 0-100%
        - Throughput: 0-10000 Kbps
        
        Returns:
            dict: Normalized values
        """
        normalized = {
            'rtt': self.normalize_value(rtt, 0, 200),
            'jitter': self.normalize_value(jitter, 0, 100),
            'loss': self.normalize_value(loss, 0, 100),
            'throughput': self.normalize_value(throughput, 0, 10000)
        }
        
        return normalized
    
    def save_to_csv(self, data):
        """
        Append data row to CSV file
        
        Args:
            data: Dictionary containing all metrics
        """
        with open(self.csv_filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                data['timestamp'],
                data['rtt'],
                data['jitter'],
                data['loss'],
                data['throughput'],
                data['moving_avg_rtt'],
                data['moving_avg_jitter'],
                data['moving_avg_loss'],
                data['normalized_rtt'],
                data['normalized_jitter'],
                data['normalized_loss'],
                data['normalized_throughput']
            ])
    
    def display_metrics(self, data):
        """
        Display current metrics in console
        
        Args:
            data: Dictionary containing all metrics
        """
        print("\n" + "="*60)
        print(f"  {data['timestamp']}")
        print("-"*60)
        print(f" RTT:            {data['rtt']:.2f} ms")
        print(f" Jitter:         {data['jitter']:.2f} ms")
        print(f" Packet Loss:    {data['loss']:.2f} %")
        print(f" Throughput:     {data['throughput']:.2f} Kbps")
        print("-"*60)
        print(f" Moving Avg RTT:    {data['moving_avg_rtt']:.2f} ms")
        print(f" Moving Avg Jitter: {data['moving_avg_jitter']:.2f} ms")
        print(f" Moving Avg Loss:   {data['moving_avg_loss']:.2f} %")
        print("-"*60)
        print(f" Normalized RTT:    {data['normalized_rtt']:.3f}")
        print(f" Normalized Jitter: {data['normalized_jitter']:.3f}")
        print(f" Normalized Loss:   {data['normalized_loss']:.3f}")
        print(f" Normalized Throughput:   {data['normalized_throughput']:.3f}")
        print("="*60)
    
    def run(self, duration=None):
        """
        Main monitoring loop - collects data every second
        
        Args:
            duration: How many seconds to run (None = run indefinitely)
        """
        print("\n" + "="*60)
        print(" STARTING NETWORK QUALITY MONITOR")
        print("="*60)
        print(f" Target Website: {self.target}")
        if self.resolved_ip and self.resolved_ip != self.target:
            print(f" Target IP:      {self.resolved_ip}")
        print(f" Window Size:    {self.window_size} samples")
        print(f" Saving to:      {self.csv_filename}")
        print("="*60)
        print(" Pinging {0} every second...\n Press Ctrl+C to stop".format(self.target))
        print("="*60 + "\n")
        
        start_time = time.time()
        
        try:
            while True:
                # Check if duration limit reached
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Execute ping
                rtt = self.ping_once()
                self.total_pings += 1
                
                if rtt is None:
                    # Ping failed
                    self.failed_pings += 1
                    rtt = 0.0  # Use 0 for failed pings
                
                # Calculate metrics
                jitter = self.calculate_jitter(rtt) if rtt > 0 else 0.0
                loss = self.calculate_packet_loss()
                throughput = self.estimate_throughput(rtt)
                
                # Update sliding windows
                if rtt > 0:
                    self.rtt_window.append(rtt)
                self.jitter_window.append(jitter)
                self.loss_window.append(loss)
                
                # Calculate moving averages
                moving_avg_rtt = self.calculate_moving_average(self.rtt_window)
                moving_avg_jitter = self.calculate_moving_average(self.jitter_window)
                moving_avg_loss = self.calculate_moving_average(self.loss_window)
                
                # Normalize features
                normalized = self.normalize_features(rtt, jitter, loss, throughput)
                
                # Prepare data dictionary
                data = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'rtt': rtt,
                    'jitter': jitter,
                    'loss': loss,
                    'throughput': throughput,
                    'moving_avg_rtt': moving_avg_rtt,
                    'moving_avg_jitter': moving_avg_jitter,
                    'moving_avg_loss': moving_avg_loss,
                    'normalized_rtt': normalized['rtt'],
                    'normalized_jitter': normalized['jitter'],
                    'normalized_loss': normalized['loss'],
                    'normalized_throughput': normalized['throughput']
                }
                
                # Save to CSV
                self.save_to_csv(data)
                
                # Display to console
                self.display_metrics(data)
                
                # Wait 1 second before next ping
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n Monitoring stopped by user")
            self.print_summary()
    
    def print_summary(self):
        """Print final statistics"""
        print("\n" + "="*60)
        print(" MONITORING SUMMARY")
        print("="*60)
        print(f"Total Pings:        {self.total_pings}")
        print(f"Failed Pings:       {self.failed_pings}")
        print(f"Success Rate:       {((self.total_pings - self.failed_pings) / self.total_pings * 100):.2f}%")
        print(f"Data saved to:      {self.csv_filename}")
        print("="*60)


def test_ping(target):
    """Test if target responds to ping"""
    try:
        result = subprocess.run(
            ['ping', '-n', '2', target],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Check if we got any successful replies
        if 'Reply from' in result.stdout:
            return True
        return False
    except Exception:
        return False


def get_user_input():
    """
    Get website name from user and validate it
    
    Returns:
        tuple: (target, csv_filename)
    """
    print("\n" + "="*60)
    print("  NETWORK QUALITY MONITOR")
    print("="*60)
    print("\n NOTE: Many websites block ping for security.")
    print(" Recommended targets that respond to ping:")
    print("   - google.com")
    print("   - 8.8.8.8 (Google DNS)")
    print("   - 1.1.1.1 (Cloudflare DNS)")
    print("   - bing.com")
    print("="*60)
    
    while True:
        # Get website name from user
        target = input("\n Enter website name or IP address (e.g., google.com): ").strip()
        
        if not target:
            print(" Please enter a valid website or IP address.")
            continue
        
        # Remove http:// or https:// if user included it
        if target.startswith("http://"):
            target = target[7:]
        elif target.startswith("https://"):
            target = target[8:]
        
        # Remove trailing slash if present
        target = target.rstrip('/')
        
        # Create a meaningful filename based on the target
        safe_filename = target.replace('.', '_').replace('/', '_').replace(':', '_')
        csv_filename = f"network_data_{safe_filename}.csv"
        
        print(f"\n Target set to: {target}")
        print(f" Data will be saved to: {csv_filename}")
        
        # Test if target responds to ping
        print(f"\n Testing if {target} responds to ping...")
        if test_ping(target):
            print(f" SUCCESS: {target} responds to ping!")
        else:
            print(f" WARNING: {target} does NOT respond to ping!")
            print(f" This target may block ICMP packets.")
            print(f" You can continue, but you'll get 100% packet loss.")
            print(f"\n Suggested alternatives:")
            print(f"   - google.com")
            print(f"   - 8.8.8.8")
            retry = input(f"\n Try a different target? (y/n): ").strip().lower()
            if retry in ['y', 'yes']:
                continue
        
        # Ask for confirmation
        confirm = input("\n Start monitoring? (y/n): ").strip().lower()
        if confirm in ['y', 'yes', '']:
            return target, csv_filename
        elif confirm in ['n', 'no']:
            print("\n Let's try again...\n")
            continue
        else:
            print(" Invalid input. Please enter 'y' or 'n'.")


if __name__ == "__main__":
    # Get user input
    target, csv_filename = get_user_input()
    
    # Create monitor instance with user-specified target
    monitor = NetworkMonitor(
        target=target,              # User-specified website
        window_size=20,             # Keep last 20 samples for moving average
        csv_filename=csv_filename   # Save to website-specific CSV file
    )
    
    # Start monitoring (runs indefinitely until Ctrl+C)
    monitor.run()
