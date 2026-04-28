# Network Monitor Update Summary

## ✅ What's Been Implemented

### 1. **Interactive Website Input**
- The script now prompts users to enter a website name or IP address
- Automatically sanitizes input (removes http://, https://, trailing slashes)
- Validates and confirms input before starting monitoring

### 2. **Custom CSV Files per Website**
- Each monitored website gets its own unique CSV file
- Example: monitoring `google.com` creates `data/network_data_google_com.csv`
- Makes it easy to compare multiple websites

### 3. **Complete Metrics Calculated**
For any website you enter, the script calculates:

#### Real-Time Metrics:
- ✅ **RTT (Round-Trip Time)**: Latency in milliseconds
- ✅ **Jitter**: Variation in delay (network stability)
- ✅ **Packet Loss**: Percentage of failed pings
- ✅ **Throughput**: Estimated data transfer rate in Kbps

#### Moving Averages:
- ✅ Moving average of RTT (smoothed)
- ✅ Moving average of Jitter
- ✅ Moving average of Packet Loss

#### Normalized Values (0-1 scale):
- ✅ Normalized RTT
- ✅ Normalized Jitter
- ✅ Normalized Loss
- ✅ Normalized Throughput

### 4. **Test Script**
- Created `test_website_monitor.py` for quick testing
- Tests monitoring for 10 seconds without interactive input
- Useful for validation and demonstrations

---

## 🚀 How to Use

### Method 1: Interactive Mode (Recommended)
```bash
python network_monitor.py
```

Then enter any website:
- `google.com`
- `github.com`
- `youtube.com`
- `amazon.com`
- `8.8.8.8` (IP addresses work too!)

### Method 2: Quick Test
```bash
python test_website_monitor.py
```

This monitors `google.com` for 10 seconds as a demo.

---

## 📊 What You Get

### Real-Time Display
Every second, you'll see:
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

### CSV File
All data is saved with these columns:
1. Timestamp
2. RTT (ms)
3. Jitter (ms)
4. Packet Loss (%)
5. Throughput (Kbps)
6. Moving Avg RTT
7. Moving Avg Jitter
8. Moving Avg Loss
9. Normalized RTT
10. Normalized Jitter
11. Normalized Loss
12. Normalized Throughput

---

## 💡 Use Cases

### 1. Compare Website Performance
Monitor different websites to see which has better response times:
- Google vs Bing
- Different CDN providers
- Your own services vs competitors

### 2. Troubleshoot Network Issues
Identify if the problem is:
- High RTT → Server is slow/far away
- High Jitter → Unstable connection
- Packet Loss → Network reliability issues

### 3. Monitor ISP Quality
Test your internet connection at different times:
- Peak hours vs off-peak
- Weekdays vs weekends
- Identify patterns and congestion

### 4. Gaming/Streaming Pre-check
Before starting a live stream or gaming session, check:
- RTT < 50ms ✅
- Jitter < 10ms ✅
- Packet Loss = 0% ✅

---

## 📁 Files Modified/Created

### Modified:
1. `network_monitor.py`
   - Added `get_user_input()` function
   - Interactive website input
   - Automatic CSV filename generation
   - URL sanitization

2. `README.md`
   - Updated with new interactive features
   - Added metrics explanations
   - Added practical use cases
   - Added example outputs

### Created:
1. `test_website_monitor.py`
   - Quick test script for validation
   - Monitors google.com for 10 seconds
   - No interactive input required

2. `UPDATE_SUMMARY.md` (this file)
   - Complete summary of changes

---

## ✅ Testing Completed

Tested successfully with:
- ✅ `google.com` - Working perfectly
- ✅ RTT calculation - Accurate
- ✅ Jitter calculation - Accurate
- ✅ Throughput estimation - Working
- ✅ Moving averages - Calculating correctly
- ✅ Normalized values - Scaling properly
- ✅ CSV file generation - Creating with all columns
- ✅ Data persistence - Saving every second

---

## 🎯 Example Session

```
> python network_monitor.py

============================================================
  🌐 NETWORK QUALITY MONITOR
============================================================

📍 Enter website name or IP address (e.g., google.com): youtube.com

✓ Target set to: youtube.com
✓ Data will be saved to: data/network_data_youtube_com.csv

▶ Start monitoring? (y/n): y

✓ Created CSV file: data/network_data_youtube_com.csv

 Starting Network Quality Monitor
 Target: youtube.com
 Window Size: 20
 Saving to: data/network_data_youtube_com.csv

 Collecting data every second... (Press Ctrl+C to stop)

[Real-time metrics display...]

^C

⏹  Monitoring stopped by user

============================================================
📊 MONITORING SUMMARY
============================================================
Total Pings:        125
Failed Pings:       0
Success Rate:       100.00%
Data saved to:      data/network_data_youtube_com.csv
============================================================
```

---

## 📌 Key Features

✅ User-friendly interactive prompts
✅ Supports any website or IP address
✅ Automatic input validation and sanitization
✅ Unique CSV files for each website
✅ Real-time metrics display
✅ Comprehensive data collection
✅ Moving averages for trend analysis
✅ Normalized values for ML-ready data
✅ Summary statistics on exit
✅ Easy to use and understand

---

## 🔧 Technical Details

- **Language**: Python 3.x
- **OS**: Windows (uses Windows ping command)
- **Dependencies**: Standard library only (subprocess, re, time, csv, os, datetime, collections, statistics)
- **Data Collection Rate**: Every 1 second
- **Window Size**: Last 20 samples (configurable)
- **Normalization Range**: 0-1 scale (0=best, 1=worst for RTT/jitter/loss)

---

## 📊 Ready for Phase 2

The collected data is now ready for:
- Machine Learning model training
- Time series analysis
- Quality prediction
- Pattern recognition
- Anomaly detection

All metrics are properly normalized and structured for ML pipelines.
