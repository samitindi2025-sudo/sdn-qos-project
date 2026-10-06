# SDN-Based Dynamic QoS Socket Network

## Project Overview

This project implements a Software Defined Network (SDN) using Mininet, Open vSwitch, and an OS-Ken OpenFlow 1.3 controller. UDP socket applications generate traffic with different QoS classes.

## Traffic Classes

| UDP Port | Class | Base Priority |
|---|---|---:|
| 5001 | HIGH | 100 |
| 5002 | MEDIUM | 50 |
| 5003 | LOW | 10 |

## Network Topology

- h1, h2, h3
- One OpenFlow 1.3 switch: s1
- Remote OS-Ken controller
- h1: 10.0.0.1
- h2: 10.0.0.2
- h3: 10.0.0.3

## Socket Application

The UDP client sends packets containing:

- Sequence number
- Timestamp
- Payload

The UDP server records:

- Packet size
- Source address
- Reception timestamp

## Dynamic SDN Behavior

When the application sends a `CONGESTION` event to the controller:

1. The controller receives the event on UDP port 9000.
2. HIGH-priority UDP 5001 traffic receives a dynamic OpenFlow priority of 200.
3. Traffic is forwarded from h1 to h2 using the dynamic rule.

When a `RECOVERY` event is received:

1. The controller removes the priority-200 rule.
2. Normal HIGH traffic priority 100 is restored.

## Congestion Scenario

A controlled bottleneck was created using Linux traffic control:

- Rate: 50 kbit/s
- Burst: 1000 bytes
- Latency: 100 ms

This was used to demonstrate behavior under network congestion.

## Testing Results

- Basic h1-h2 connectivity: 0% packet loss
- UDP socket test: 10/10 packets received
- Normal HIGH UDP flow: 20 packets matched the priority-100 h1-to-h2 rule
- Dynamic flow: priority-200 successfully installed
- Dynamic flow test: 1000 UDP packets generated; 92 packets (98,072 bytes) matched the priority-200 rule
- Recovery: priority-200 dynamic rule successfully removed

## Running the Project

### Start Controller

```bash
python -c "from os_ken.base import app_manager; app_manager.AppManager.run_apps(['os_ken.controller.ofp_handler','controller.qos_controller'])"
EOD
