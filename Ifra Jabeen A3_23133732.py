import pexpect
import difflib

# Define device details
ip_address = '192.168.56.101'
username = 'cisco'
password = 'cisco123!'
new_hostname = 'HostName1'
loopback_ip = '10.0.0.1'
loopback_mask = '255.255.255.255'
interface_ip = '192.168.1.1'
interface_mask = '255.255.255.0'
ospf_process_id = '1'
eigrp_as_number = '100'
rip_version = '2'
network_to_advertise = '10.0.0.0'
wildcard_mask = '0.0.0.255'
area_id = '0'
baseline_file = 'baseline_config.txt'  # Local baseline configuration file

# Create SSH session
session = pexpect.spawn(f'ssh {username}@{ip_address}', encoding='utf-8', timeout=20)
result = session.expect(['Password: ', pexpect.TIMEOUT, pexpect.EOF])

# Check for session creation success
if result != 0:
    print('--- ERROR! Cannot create a session for:', ip_address)
    exit()

# Enter password for SSH
session.sendline(password)
result = session.expect(['#', pexpect.TIMEOUT, pexpect.EOF])

if result != 0:
    print('--- ERROR! Incorrect password or unable to log in.')
    exit()

# Enter configuration mode
session.sendline('configure terminal')
result = session.expect([r'\(config\)#', pexpect.TIMEOUT, pexpect.EOF])

if result != 0:
    print('--- ERROR! Entering configuration mode failed.')
    exit()

# Modify hostname
session.sendline(f'hostname {new_hostname}')
result = session.expect([rf'{new_hostname}\(config\)#', pexpect.TIMEOUT, pexpect.EOF])

if result != 0:
    print('--- ERROR! Modifying hostname failed.')
    exit()

# Configure loopback interface
session.sendline('interface loopback0')
session.expect([r'\(config-if\)#', pexpect.TIMEOUT])
session.sendline(f'ip address {loopback_ip} {loopback_mask}')
session.expect([r'\(config-if\)#', pexpect.TIMEOUT])
print('--- Configured loopback interface with IP:', loopback_ip)

# Configure another interface
session.sendline('interface GigabitEthernet0/1')
session.expect([r'\(config-if\)#', pexpect.TIMEOUT])
session.sendline(f'ip address {interface_ip} {interface_mask}')
session.expect([r'\(config-if\)#', pexpect.TIMEOUT])
session.sendline('no shutdown')
session.expect([r'\(config-if\)#', pexpect.TIMEOUT])
print('--- Configured GigabitEthernet0/1 with IP:', interface_ip)

# Configure OSPF
session.sendline(f'router ospf {ospf_process_id}')
session.expect([r'\(config-router\)#', pexpect.TIMEOUT])
session.sendline(f'network {network_to_advertise} {wildcard_mask} area {area_id}')
session.expect([r'\(config-router\)#', pexpect.TIMEOUT])
print(f'--- Configured OSPF with process ID {ospf_process_id} and advertised network {network_to_advertise}/{wildcard_mask}')

# Configure EIGRP
session.sendline(f'router eigrp {eigrp_as_number}')
session.expect([r'\(config-router\)#', pexpect.TIMEOUT])
session.sendline(f'network {network_to_advertise} {wildcard_mask}')
session.expect([r'\(config-router\)#', pexpect.TIMEOUT])
print(f'--- Configured EIGRP with AS number {eigrp_as_number} and advertised network {network_to_advertise}/{wildcard_mask}')

# Configure RIP
session.sendline(f'router rip')
session.expect([r'\(config-router\)#', pexpect.TIMEOUT])
session.sendline(f'version {rip_version}')
session.expect([r'\(config-router\)#', pexpect.TIMEOUT])
session.sendline(f'network {network_to_advertise}')
session.expect([r'\(config-router\)#', pexpect.TIMEOUT])
print(f'--- Configured RIP version {rip_version} and advertised network {network_to_advertise}')

# Exit configuration mode
session.sendline('end')
session.expect(['#', pexpect.TIMEOUT])

# Save the current running configuration to a file locally
session.sendline('show running-config')
session.expect(['#', pexpect.TIMEOUT])
with open('running_config_telnet.txt', 'w') as f:
    f.write(session.before)

# Compare current running configuration with startup configuration
session.sendline('show archive config differences running-config startup-config')
session.expect(['#', pexpect.TIMEOUT])
print("\n--- Differences between running-config and startup-config ---")
print(session.before)

# Open 'running_config_telnet.txt' in read-only mode
with open('running_config_telnet.txt', 'r') as f:
    running_config = f.readlines()

# Try to open the baseline configuration file in read mode only
try:
    with open(baseline_file, 'r') as f:
        baseline_config = f.readlines()
except FileNotFoundError:
    print(f'--- ERROR! Baseline file "{baseline_file}" not found ---')
    baseline_config = []

# Compare baseline configuration with the running configuration
if baseline_config:
    diff = difflib.unified_diff(baseline_config, running_config, fromfile=baseline_file, tofile='running_config_telnet.txt')
    print("\n--- Differences between baseline and current running-config ---")
    for line in diff:
        print(line, end='')

# Display success message
print('\nConnection is successful to:', ip_address)
print('                   Username:', username)
print('                   Password:', password)
print('                  New Hostname:', new_hostname)

# Terminate the session
session.sendline('quit')
session.close()
