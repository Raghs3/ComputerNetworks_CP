# 🌐 Real-Time Network Quality Prediction System

## Phase 1: Data Collection & Feature Extraction

### ✅ Implemented Features

1. **Ping Automation Script**
   - Automatically pings target every second
   - Captures Round-Trip Time (RTT)

2. **Metric Calculation**
   - **RTT (Round-Trip Time)**: Delay for packet to go and return
   - **Jitter**: Variation between consecutive delays (network stability indicator)
   - **Packet Loss**: Percentage of failed pings
   - **Throughput**: Estimated data transfer rate based on RTT

3. **Moving Averages**
   - Calculates moving average for RTT, Jitter, and Loss
   - Uses sliding window (default: last 20 samples)
   - Smooths out spikes to show real trends

4. **Feature Normalization**
   - Converts all metrics to 0-1 scale
   - Makes features comparable for future ML models
   - Uses min-max normalization

5. **CSV Data Storage**
   - All metrics saved in real-time to `network_data.csv`
   - Includes timestamp, raw values, moving averages, and normalized features

---

## 🚀 How to Run

### Prerequisites
- Python 3.x installed
- Windows OS (script uses Windows ping command)

### Run the Script

```bash
python network_monitor.py
```

### Input Required
When you run the script, you'll be prompted to enter a website name:

```
============================================================
  🌐 NETWORK QUALITY MONITOR
============================================================

📍 Enter website name or IP address (e.g., google.com): google.com

✓ Target set to: google.com
✓ Data will be saved to: network_data_google_com.csv

▶ Start monitoring? (y/n): y
```

**Examples of valid inputs:**
- `google.com`
- `github.com`
- `8.8.8.8`
- `youtube.com`
- `amazon.com`
- `facebook.com`
- `twitter.com`

**Note:** The script automatically handles URLs - you can enter just the domain name without `http://` or `https://`

The script will:
1. Accept your website input
2. Automatically sanitize the website name
3. Create a unique CSV file named `network_data_<website>.csv` (e.g., `network_data_google_com.csv`)
4. Start monitoring and display real-time metrics every second
5. Save all data to the CSV file for later analysis

### Stop Monitoring
Press `Ctrl+C` to stop and see summary statistics

```
⏹  Monitoring stopped by user

============================================================
📊 MONITORING SUMMARY
============================================================
Total Pings:        245
Failed Pings:       2
Success Rate:       99.18%
Data saved to:      network_data_google_com.csv
============================================================
```

### Quick Test (Optional)
Want to test without interactive input? Run the test script:

```bash
python test_website_monitor.py
```

This will monitor `google.com` for 10 seconds and save results to `test_google_com.csv`.

---

## 📊 Output Format

### Console Display
Real-time metrics displayed every second:
```
============================================================
  2026-03-09 21:50:35
------------------------------------------------------------
 RTT:            32.00 ms
 Jitter:         5.00 ms
 Packet Loss:    0.00 %
 Throughput:     8.00 Kbps
------------------------------------------------------------
 Moving Avg RTT:    34.50 ms
 Moving Avg Jitter: 3.20 ms
 Moving Avg Loss:   0.00 %
------------------------------------------------------------
 Normalized RTT:    0.160
 Normalized Jitter: 0.050
 Normalized Loss:   0.000
 Normalized Throughput:   0.001
============================================================
```

### CSV File (`network_data_<website>.csv`)
All data is saved to a CSV file with the following columns:

| Timestamp | RTT (ms) | Jitter (ms) | Packet Loss (%) | Throughput (Kbps) |
|-----------|----------|-------------|-----------------|-------------------|
| 2026-03-09 21:50:35 | 32.0 | 0.0 | 0.0 | 8.0 |
| 2026-03-09 21:50:37 | 37.0 | 5.0 | 0.0 | 6.92 |
| 2026-03-09 21:50:38 | 25.0 | 12.0 | 0.0 | 10.24 |

Additional columns include:
- Moving Avg RTT, Moving Avg Jitter, Moving Avg Loss
- Normalized RTT, Normalized Jitter, Normalized Loss, Normalized Throughput

**Each website gets its own CSV file:**
- `network_data_google_com.csv`
- `network_data_github_com.csv`
- `network_data_youtube_com.csv`
- etc.

---

## 📊 Understanding the Metrics

### 📡 RTT (Round-Trip Time)
- **What it is**: Time taken for a packet to travel from your computer to the website and back
- **Unit**: Milliseconds (ms)
- **Good values**: < 50ms (excellent), 50-100ms (good), > 200ms (poor)
- **Impact**: Lower RTT = faster response times and better user experience

### 📊 Jitter
- **What it is**: Variation in delay between consecutive packets
- **Unit**: Milliseconds (ms)
- **Good values**: < 10ms (excellent), 10-30ms (acceptable), > 50ms (problematic)
- **Impact**: High jitter = unstable connection, important for video calls and gaming

### ❌ Packet Loss
- **What it is**: Percentage of packets that don't reach their destination
- **Unit**: Percentage (%)
- **Good values**: 0% (perfect), < 1% (acceptable), > 5% (poor)
- **Impact**: Causes stuttering in video/audio and slower data transfers

### ⚡ Throughput
- **What it is**: Estimated data transfer rate based on RTT
- **Unit**: Kilobits per second (Kbps)
- **Note**: This is an estimation based on ping packet size
- **Impact**: Higher throughput = faster downloads/uploads

---

## 📈 Advanced Features

### Moving Averages
The script calculates rolling averages of the last 20 measurements to:
- Smooth out temporary spikes or drops
- Show real trends in network quality
- Reduce noise from single anomalous readings

### Normalized Values
All metrics are normalized to a 0-1 scale:
- Makes different metrics comparable
- Useful for machine learning models
- 0 = best performance, 1 = worst performance (for RTT, jitter, loss)

---

## ⚙️ Configuration

### Interactive Mode (Default)
The script will prompt you to enter a website when you run it. This is the recommended way to use the tool.

### Manual Configuration (Advanced)
If you want to hardcode a target, you can modify the `__main__` section in `network_monitor.py`:

```python
if __name__ == "__main__":
    monitor = NetworkMonitor(
        target="your-website.com",     # Change to your desired target
        window_size=20,                 # Change moving average window size
        csv_filename="custom_name.csv"  # Change output filename
    )
    monitor.run()
```

### Key Parameters:
- **target**: Website name (e.g., "google.com") or IP address (e.g., "8.8.8.8")
- **window_size**: Number of recent samples for moving average calculation (default: 20)
- **csv_filename**: Name of the output CSV file

---

## 💡 Practical Use Cases

### 1. Compare Website Performance
Monitor multiple websites to compare their network performance:

```bash
# Run 1: Monitor Google
python network_monitor.py
# Enter: google.com

# Run 2: Monitor GitHub
python network_monitor.py
# Enter: github.com

# Run 3: Monitor YouTube
python network_monitor.py
# Enter: youtube.com
```

Then compare the CSV files to see which service has better response times.

### 2. Troubleshoot Slow Website
If a specific website is slow, monitor it to identify the issue:

```bash
python network_monitor.py
# Enter: slow-website.com
```

Watch for:
- **High RTT**: Website server is far away or slow
- **High Jitter**: Unstable connection
- **Packet Loss**: Network reliability issues

### 3. Monitor Your ISP Quality
Test your internet connection quality using a reliable target:

```bash
python network_monitor.py
# Enter: 8.8.8.8  (Google DNS)
```

Run during different times of day to identify:
- Peak congestion hours
- Connection stability patterns
- Average performance baseline

### 4. Gaming/Streaming Analysis
Check if your connection is suitable for real-time applications:

```bash
python network_monitor.py
# Enter: twitch.tv  (or your gaming server)
```

For gaming/streaming you want:
- RTT < 50ms
- Jitter < 10ms
- Packet Loss = 0%

---

## 🎯 Next Steps (Not Implemented Yet)

- Machine learning model for quality prediction
- Graphical visualization
- Real-time alerts
- Quality classification (Good/Congested/Poor)
- Trend forecasting

---

## 📝 Notes

- Script requires internet connection
- Uses ICMP ping (may require admin privileges on some networks)
- Data collection is continuous until manually stopped
- Each website gets its own CSV file for easy comparison
