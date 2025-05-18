#!/bin/sh

#routing table
ip rule add from 192.168.0.171 table 1
ip rule add from 192.168.0.166 table 2
ip rule add from 192.168.0.232 table 3

ip route add 192.168.0.0/24 dev enp2s0 scope link table 1
ip route add default via 192.168.0.1 dev enp2s0 table 1

ip route add 192.168.0.0/24 dev enx001788f82a14 scope link table 2 
ip route add default via 192.168.0.182 dev enx001788f82a14 table 2

ip route add 192.168.0.0/24 dev wlp3s0 scope link table 3
ip route add default via 192.168.0.1 dev wlp3s0 table 3

#ethernet link with 20ms delay and 10ms jitter
tc qdisc add dev enp2s0 root netem delay 20ms 10ms


