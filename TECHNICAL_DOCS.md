# 🧮 Technical Documentation: Metric Calculations

## Overview
This document explains how each network metric is calculated in the Network Quality Prediction System.

---

## 1️⃣ RTT (Round-Trip Time)

### What It Is
The time taken for a packet to travel from source to destination and back.

### How We Measure It
```
RTT = Time packet returns - Time packet sent
```

### Implementation
- Uses Windows `ping` command
- Extracts RTT from ping output using regex
- Pattern: `time=XXms` or `time<XXms`
- Unit: milliseconds (ms)

### Example
```
Ping output: "Reply from 8.8.8.8: bytes=32 time=23ms TTL=116"
Extracted RTT: 23 ms
```

### What Values Mean
- **0-30ms**: Excellent (local/fast network)
- **30-100ms**: Good (normal internet)
- **100-200ms**: Moderate (acceptable)
- **>200ms**: Poor (slow connection)

---

## 2️⃣ Jitter

### What It Is
The variation in delay between consecutive packets. Measures network stability.

### Formula
```
Jitter = |RTT_current - RTT_previous|
```

### Implementation
```python
jitter = abs(current_rtt - previous_rtt)
```

### Example
```
Sample 1: RTT = 20ms
Sample 2: RTT = 25ms
Jitter = |25 - 20| = 5ms

Sample 3: RTT = 22ms
Jitter = |22 - 25| = 3ms
```

### What Values Mean
- **0-10ms**: Excellent (very stable)
- **10-30ms**: Good (stable)
- **30-50ms**: Moderate (noticeable variation)
- **>50ms**: Poor (highly unstable - bad for real-time apps)

### Why It Matters
- High jitter = inconsistent network
- Critical for: VoIP, video calls, online gaming
- Low jitter = smooth experience

---

## 3️⃣ Packet Loss

### What It Is
Percentage of packets that fail to reach destination and return.

### Formula
```
Packet Loss (%) = (Failed Pings / Total Pings) × 100
```

### Implementation
```python
loss_percentage = (failed_pings / total_pings) * 100
```

### Example
```
Total pings sent: 100
Failed pings: 3
Packet Loss = (3 / 100) × 100 = 3%
```

### What Values Mean
- **0%**: Perfect (ideal)
- **0-1%**: Excellent (barely noticeable)
- **1-2.5%**: Good (acceptable)
- **2.5-5%**: Fair (noticeable in video/gaming)
- **>5%**: Poor (significant problems)

### Why It Matters
- Lost packets = missing data
- TCP retransmits lost packets (causes delay)
- UDP drops lost packets (audio/video glitches)

---

## 4️⃣ Throughput

### What It Is
Estimated data transfer capacity of the network.

### Formula (Simplified)
```
Throughput (Kbps) = (Packet Size in bits / RTT in seconds) / 1000
```

### Implementation
```python
packet_size_bits = 32 * 8  # 32 bytes = 256 bits (ping packet size)
rtt_seconds = rtt / 1000.0  # Convert ms to seconds
throughput_kbps = (packet_size_bits / rtt_seconds) / 1000
```

### Example
```
Packet size: 32 bytes = 256 bits
RTT: 20ms = 0.020 seconds

Throughput = (256 / 0.020) / 1000
          = 12800 / 1000
          = 12.8 Kbps
```

### Notes
- This is a **simplified estimation**
- Actual throughput depends on bandwidth, congestion, etc.
- Uses inverse relationship: Lower RTT → Higher throughput
- Not a direct measurement (requires actual data transfer for accurate throughput)

---

## 5️⃣ Moving Average

### What It Is
Average of the most recent N samples. Smooths out noise and shows trends.

### Formula
```
Moving Average = (Sum of last N values) / N
```

### Implementation
```python
moving_avg = sum(window) / len(window)
```

### Example (Window Size = 5)
```
RTT samples: [20, 25, 22, 30, 23]

Moving Avg = (20 + 25 + 22 + 30 + 23) / 5
           = 120 / 5
           = 24 ms

New sample arrives: 28
Window becomes: [25, 22, 30, 23, 28] (oldest removed)
New Moving Avg = (25 + 22 + 30 + 23 + 28) / 5 = 25.6 ms
```

### Why It's Used
- **Filters noise**: Single spike doesn't affect trend
- **Shows direction**: Increasing/decreasing pattern
- **Better for prediction**: More stable than raw values

### Window Size Selection
- **Small window (5-10)**: Responds quickly to changes
- **Medium window (20-50)**: Balanced (our default: 20)
- **Large window (100+)**: Very smooth, slow to respond

---

## 6️⃣ Normalization

### What It Is
Scaling all features to a common range (0 to 1) for fair comparison.

### Formula (Min-Max Normalization)
```
Normalized Value = (Value - Min) / (Max - Min)
```

### Implementation
```python
normalized = (value - min_val) / (max_val - min_val)
# Clamped to [0, 1]
```

### Example: Normalizing RTT

Assume RTT range: 0-200ms

```
RTT = 50ms
Normalized = (50 - 0) / (200 - 0) = 50 / 200 = 0.25

RTT = 100ms
Normalized = (100 - 0) / (200 - 0) = 100 / 200 = 0.50

RTT = 200ms
Normalized = (200 - 0) / (200 - 0) = 200 / 200 = 1.00
```

### Normalization Ranges Used

| Metric | Expected Range | Normalized Range |
|--------|---------------|------------------|
| RTT | 0 - 200 ms | 0.0 - 1.0 |
| Jitter | 0 - 100 ms | 0.0 - 1.0 |
| Packet Loss | 0 - 100% | 0.0 - 1.0 |
| Throughput | 0 - 10000 Kbps | 0.0 - 1.0 |

### Why Normalization Is Important

1. **Makes metrics comparable**
   - RTT (0-200) vs Loss (0-100) have different scales
   - Normalized: both are 0-1

2. **Essential for ML models**
   - Neural networks work better with normalized inputs
   - Prevents features with larger scales from dominating

3. **Easier visualization**
   - All metrics can be plotted on same graph
   - Clear comparison of network conditions

### Example Use Case
```
Raw values:
- RTT: 50ms (seems small)
- Jitter: 40ms (seems small)
- Loss: 5% (seems small)

But which is worse?

Normalized values:
- RTT: 0.25 (okay)
- Jitter: 0.40 (moderate concern)
- Loss: 0.05 (good)

Now we can see: Jitter is the biggest concern!
```

---

## 🎯 Putting It All Together

### Data Flow

```
1. Ping Target (every 1 second)
   ↓
2. Extract RTT (regex parsing)
   ↓
3. Calculate Jitter (compare with previous RTT)
   ↓
4. Track Packet Loss (count failures)
   ↓
5. Estimate Throughput (from RTT)
   ↓
6. Update Sliding Windows (store recent values)
   ↓
7. Calculate Moving Averages (smooth trends)
   ↓
8. Normalize Features (scale to 0-1)
   ↓
9. Save to CSV & Display
```

### Sample Output Interpretation

```
📡 RTT: 45.00 ms           → Current delay (moderate)
📊 Jitter: 12.00 ms        → Variation (acceptable)
❌ Packet Loss: 2.00 %     → 2% packets lost (fair)
⚡ Throughput: 5.69 Kbps   → Estimated capacity

📈 Moving Avg RTT: 48.50 ms    → Trend: delay increasing
📈 Moving Avg Jitter: 10.20 ms → Trend: stable
📈 Moving Avg Loss: 1.80 %     → Trend: consistent loss

🔢 Normalized RTT: 0.225     → 22.5% of max expected RTT
🔢 Normalized Jitter: 0.120  → 12% of max expected jitter
🔢 Normalized Loss: 0.020    → 2% of max loss range
```

### Interpretation:
- RTT is trending upward (moving avg > current) → Network getting slower
- Jitter is stable → Connection consistency is maintained
- Small packet loss → Some congestion present
- **Prediction**: Network quality is slightly degrading

---

## 🔬 Future Enhancements (Not Yet Implemented)

1. **Adaptive Normalization**: Adjust ranges based on observed data
2. **Weighted Moving Average**: Recent samples matter more
3. **Exponential Smoothing**: Better trend detection
4. **Standard Deviation**: Measure variability
5. **Correlation Analysis**: Understand metric relationships
