import os, sys, time, psutil, matplotlib

import matplotlib.pyplot as plt
matplotlib.use("TkAgg")

#Absolute file path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
# Where generated plot PNGs get saved (mirrors automation/finance.py) ──
PLOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

#Sampling parameters
SAMPLE_COUNT = 10
SAMPLE_INTERVAL = 1

def sample_metrics():
    #Timestamps for throughputs of various metrics
    timestamps, cpu_vals, ram_vals, net_sent_vals, net_recv_vals = [], [], [], [], []

    prev_net = psutil.net_io_counters()
    prev_time = time.time()

    for i in range(SAMPLE_COUNT):
        time.sleep(SAMPLE_INTERVAL)
        now = time.time()

        cpu_vals.append(psutil.cpu_percent(interval=None)) #CPU Performance metric
        ram_vals.append(psutil.virtual_memory().percent) #RAM Performance metric
 
        net_now = psutil.net_io_counters() 
        elapsed = max(now - prev_time, 0.001)
        # Convert byte deltas to KB/s for a more readable scale
        sent_rate = (net_now.bytes_sent - prev_net.bytes_sent) / elapsed / 1024 #Rate of sending 
        recv_rate = (net_now.bytes_recv - prev_net.bytes_recv) / elapsed / 1024 #Rate of receiving
        net_sent_vals.append(sent_rate)
        net_recv_vals.append(recv_rate)
 
        prev_net = net_now
        prev_time = now
        timestamps.append(i + 1)
 
    return timestamps, cpu_vals, ram_vals, net_sent_vals, net_recv_vals

def plot_performance_metrics() -> tuple[str, str]:
    timestamps, cpu_vals, ram_vals, net_sent, net_recv = sample_metrics()
    battery_percent, plugged_in = None, None
    battery = psutil.sensors_battery()
    if battery is not None:
        battery_percent, plugged_in = battery.percent, battery.power_plugged
 
    fig, axes = plt.subplots(2, 1, figsize=(8, 6))
 
    # Top chart: CPU + RAM over the sample window
    axes[0].plot(timestamps, cpu_vals, label="CPU %", color="#e74c3c")
    axes[0].plot(timestamps, ram_vals, label="RAM %", color="#3498db")
    axes[0].set_ylim(0, 100)
    axes[0].set_ylabel("Usage (%)")
    axes[0].set_xlabel("Sample (1 per second)")
    axes[0].set_title("CPU & RAM Usage")
    axes[0].legend()
    axes[0].grid(alpha=0.3)
 
    # Bottom chart: network throughput
    axes[1].plot(timestamps, net_sent, label="Upload (KB/s)", color="#9b59b6")
    axes[1].plot(timestamps, net_recv, label="Download (KB/s)", color="#2ecc71")
    axes[1].set_ylabel("KB/s")
    axes[1].set_xlabel("Sample (1 per second)")
    axes[1].set_title("Network Throughput")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
 
    battery_note = ""
    if battery_percent is not None:
        plug_text = "plugged in" if plugged_in else "on battery"
        battery_note = f" | Battery: {battery_percent:.0f}% ({plug_text})"
    fig.suptitle(f"Fairy — System Performance Snapshot{battery_note}")
    fig.tight_layout()
 
    save_path = os.path.join(PLOTS_DIR, "performance_snapshot.png")
    fig.savefig(save_path)
    plt.close(fig)
 
    avg_cpu = sum(cpu_vals) / len(cpu_vals)
    avg_ram = sum(ram_vals) / len(ram_vals)
    summary = (
        f"Over the last {SAMPLE_COUNT} seconds, average CPU usage was {avg_cpu:.0f} percent "
        f"and RAM usage was {avg_ram:.0f} percent. I've saved a performance chart for you, Master."
    )
    return summary, save_path