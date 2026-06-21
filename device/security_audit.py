import subprocess, psutil

#List out the ports to watch out for
WATCHLIST_PORTS = {
    21: "FTP",
    23: "Telnet",
    135: "RPC",
    139: "NetBIOS",
    445: "SMB",
    3389: "RDP",
}

def run_command(args: list[str]) -> str: 
    try:
        #Perform a 'read-only' operation and return the result
        result = subprocess.run(args, capture_output=True, text=True, timeout=10, shell=False) 
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return ""
    
# ========= Vulnerability Inspector (Firewall, Defender, Open Ports) ========= #

# Windows Firewall
def check_firewall() -> tuple[bool, str]:
    #Check Windows Firewall profiles via netsh
    output = run_command(["netsh", "advfirewall", "show", "allprofiles", "state"]) 
    
    #Return vulnerability report on Windows Firewall
    if not output: 
        return False, "Could not determine firewall status."
    if "ON" in output.upper() and "OFF" not in output.upper():
        return True, "Firewall is enabled on all profiles."
    if "OFF" in output.upper():
        return False, "Warning: at least one firewall profile is OFF."
    return False, "Firewall status unclear — check manually via Windows Security."

#Windows Defender
def check_defender() -> tuple[bool, str]:
    #Check Windows Defender via Powershell
    output = run_command(["powershell", "-NoProfile", "-Command", "(Get-MpComputerStatus).RealTimeProtectionEnabled"])
    cleaned = output.strip().lower()

    #Return vulnerability report on Windows Defender
    if cleaned == "true":
        return True, "Windows Defender real-time protection is enabled."
    if cleaned == "false":
        return False, "Warning: Windows Defender real-time protection is OFF."
    return False, "Could not determine Defender status — you may be running third-party antivirus instead."
 
def check_open_ports() -> tuple[bool, str]:
    #Checks local listening ports against the watchlist using psutil, but only within the local device (no remote scanning or pinging)
    try:
        connections = psutil.net_connections(kind="inet") #Acquire the connections via psutil
    except(psutil.AccessDenied, PermissionError): #Throw exception if access was forbidden
        return False, "Could not check open ports — try running as Administrator for full results."
    listening_watchlist_hits = set()
    for conn in connections(): #For each of the open port connections...
        if conn.status == psutil.CONN_LISTEN and conn.laddr: #If a port is actively listening and also has a local address
            port = conn.laddr.port #Acquire that said local address
            if port in WATCHLIST_PORTS: #If one of the actively listening ports is in the list of ports to check
                listening_watchlist_hits.add(port) #Add it to the list (we'll use this later)
    if not listening_watchlist_hits:
        return True, "No commonly-risky ports found listening." 
    names = [f"{p} ({WATCHLIST_PORTS[p]})" for p in sorted(listening_watchlist_hits)]
    return False, f"Warning: found watchlisted ports listening: {', '.join(names)}." #Flag a watchlisted port that's actively listening and susceptible to attacks


def run_security_audit() -> str: #Run all three security checks
    #All three security checker functions called out
    security_checks = [
        ("Firewall", check_firewall()),
        ("Defender", check_defender()),
        ("Open ports", check_open_ports()),
    ]

    passed = sum(1 for _, (ok, _) in security_checks if ok)
    lines = [f"Security check complete, Master. {passed} out of {len(security_checks)} checks look good."]
    for name, (ok, message) in security_checks:
        status = "OK" if ok else "FLAGGED"
        lines.append(f"{name} — {status}: {message}")
 
    return " ".join(lines)
 

