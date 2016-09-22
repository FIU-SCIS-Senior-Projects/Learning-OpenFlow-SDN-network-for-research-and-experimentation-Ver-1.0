#!/bin/sh

i=1

while [ $i -le 5 ]
do
	sudo ovs-ofctl add-flow "sw${i}" in_port=1,actions=output:3
	sudo ovs-ofctl add-flow "sw${i}" in_port=2,actions=output:3
	sudo ovs-ofctl add-flow "sw${i}" in_port=3,actions=output:2
	i=$(( $i+1 ))
done
