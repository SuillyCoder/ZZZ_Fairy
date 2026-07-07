#Background daemon that constantly checks memory %
#and automatically clears based on set threshold 

import threading, time, gc, os, psutil
from device.system_info import preview_cache_clear, clear_cache

MEMORY_THRESHOLD = 75 #Memory cap threshold
POLL_INTERVAL_SECONDS = 30 #How often to check memory
COOLDOWN_SECONDS = 300 #Time to wait until next re-trigger

IS_WINDOWS = (os.name == "nt") #Checks if the operating system is Windows

if IS_WINDOWS:
    import ctypes
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_SET_QUOTA = 0x0100
    _kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    _psapi = ctypes.WinDLL('psapi', use_last_error = True)

#Ask Windows to trim one process' working set  to page out unused memory
def empty_working_set(pid: int) -> bool: 
    if not IS_WINDOWS:
        return False
    handle = _kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA, False, pid)
    if not handle:
        return False
    try:
        return bool(_psapi.EmptyWorkingSet(handle))
    finally: 
        _kernel32.CloseHandle(handle)

#Trim all the unnecessary proceses
def trim_all_processes() -> tuple[int, int]:
    succeeded = 0 
    total = 0
    for proc in psutil.process_iter(['pid']):
        total += 1
        try:
            if empty_working_set(proc.info['pid']):
                succeeded += 1
        except Exception:
            continue
        return succeeded, total
    
#Run all three memory cleanup processes and voice them out in a log
def free_up_memory() -> str:
    results = []
    
    #Pass 1: Temp Cache
    summary, temp_dir = preview_cache_clear()

    #Pass 2: Fairy's own garbage collection
    collected = gc.collect()
    results.append(f"Garbage-collected {collected} objects from my own memory.")

    #Pass 3: Other miscellaneous processes
    if IS_WINDOWS: 
        succeeded, total = trim_all_processes()
        results.append(f"Trimmed {succeeded}/{total} process working sets.")
    else:
        results.append("Skipped working-set trim — that step is Windows-only.")

    return " ".join(results)

#Function to monitor the memory of the system
def start_memory_monitor(
    speak_fn=None, threshold=MEMORY_THRESHOLD,
    poll_interval=POLL_INTERVAL_SECONDS,
    cooldown=COOLDOWN_SECONDS):

    def _loop():
        last_triggered = 0
        while True:
            percent = psutil.virtual_memory().percent #Acquire the percentage of memory
            now = time.time() #Get the current time

            if percent >= threshold and (now - last_triggered) >= cooldown:
                print(f"[MemoryDaemon] RAM at {percent:.0f}% — freeing memory.")
                
                if speak_fn:
                    speak_fn(f"Memory's at {percent:.0f} percent, Master. Freeing some up now.")
                summary = free_up_memory()
                print(f"[MemoryDaemon] {summary}")
                last_triggered = now
            time.sleep(poll_interval)
            
    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread
