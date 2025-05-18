#!/bin/sh

cd ../src/reles/kernel
make
sudo insmod mptcp_reles.ko

cd ../../falcon/kernel
make
sudo insmod mptcp_falcon.ko
