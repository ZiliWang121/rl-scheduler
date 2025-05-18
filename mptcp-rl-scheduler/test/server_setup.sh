#!/bin/sh

#routing table
#ip rule add from 192.168.0.101 table 1
#ip rule add from 192.168.0.182 table 2
#ip rule add from 192.168.0.193 table 3

#ip route add 192.168.0.0/24 dev enp2s0 scope link table 1
#ip route add default via 192.168.0.1 dev enp2s0 table 1

#ip route add 192.168.0.0/24 dev enx001788f81b24 scope link table 2
#ip route add default via 192.168.0.166 dev enx001788f81b24 table 2

#ip route add 192.168.0.0/24 dev wlp3s0 scope link table 3
#ip route add default via 192.168.0.1 dev wlp3s0 table 3

