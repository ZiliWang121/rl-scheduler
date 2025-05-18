# MPTCP RL Scheduler

## Description
Implementation of multiple RL based MPTCP schedulers.

ReLes (https://ieeexplore.ieee.org/document/8737649) employs DRL, in particular a NAF network to derive a scheduling policy maximizing multitude of QoL services such as throughput,delay and packet loss. Additionally training is performed asynchronous and after every episode the Agent used to derive the scheduling policy is updated

FALCON (arxiv.org/pdf/2201.08969.pdf) leverages reptile meta learner to take advantage of both offline and online learning. In the offline learning loop multiple meta models are trained depending on a combination of network characteristics. Afterwards in the online learning loop if a change is detected in the network characteristics the appropriate meta model is trained using K-shot optimization. The DQN Agent is then used to derive the new scheduling policy. Current implementation does not ignore the CWND when scheduling packets in the action space. 

## Installation
Need atleast Python3.8.10 with mininet/mininet-wifi (https://mininet-wifi.github.io/get-started/) installed
Additionally to use MPTCP and the custom kernel implementations donwload all .deb files and install them (https://multipath-tcp.org/pmwiki.php/Users/AptRepository).

## Usage
Install all neccessary kernel .deb packages, for the custom kernel with reles/falcon, from the cloud with sudo dpkg -i linux*.deb
Download all the wanted test files and add them to every scheduler folder to test with. \
Using MPTCP_test.py all schedulers can be tested in Mininet with following arguments \
--action: decides wheter to debug (0), test one scheduler (1) or test all schedulers (2) \
--scheduler: decides which scheduler to test with (0,1,2,3,4,5) = (deafult,blest,reles,falcon,reles-ext,falcon-ext) \
--scenario: runs the equivalent scenario depening on wheter scenario contains static or dynamic \
Using mininet_wifi.py all schedulers can be tested in mininet-wifi with the same arguments \
Due to an unresolbed issue to test all schedulers in mininet-wifi run the ./test_all.sh script insead of --action 2 \
To debug with action (0) run server.py and client.py on the respective mininet hosts using the consoles created from MPTCP_test.py. Host 2 is currently performing the role of a server and the client request a file download of 2 MB. This bulk transfer is performed 120 times independently and the MPTCP connection is restarted after every finished transfer. \
When all schedulers have been tested atleast once for the same scenario the corresponding results are collected in test-results and can be
evaluated using eval.py script

## Contributing
After making changes to mpsched.c recompile to create new .so file
When making changes to the kernel modules compile with "make" and install/remove module with "sudo insamod/rmmod module.ko"


