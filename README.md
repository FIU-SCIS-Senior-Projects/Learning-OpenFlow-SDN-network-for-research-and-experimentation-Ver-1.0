# Learning-OpenFlow-SDN-network-for-research-and-experimentation-Ver-1.0

## Installation

### Prerequisites
* Some virtualization software (VirtualBox, VMWare, etc.)
* Mininet VM
* Note: You can download both these things by viewing the [Mininet setup guide](http://mininet.org/download/)
* OFTest
* Ryu

#### OFTest Installation
* Clone the OFTest git repo in your home directory with `git clone git://github.com/floodlight/oftest ~/`
	* If you encounter any issues installing OFTest, refer the [official documentation](https://github.com/floodlight/oftest#getting-oftest)
	
#### Ryu Installation
* Clone the Ryu git repo in your home directory with `git clone git://github.com/osrg/ryu.git ~/`
* Navigate to the new repo with `cd ~/ryu`
* Run `python setup.py install`
	* If you have a permission denied error, run with `sudo` or as root

### SwitchTester
* Clone the SwitchTester git repo in your home directory with `git clone `.
* Pull the develop branch with `git pull origin develop` or the switch-tester branch with `git pull origin switch-tester`
* Navigate to the new repo with `cd Learning-OpenFlow-SDN-network-for-research-and-experimentation-Ver-1.0`
* Run `python setup.py install`
	* If you have a permission denied error, run with `sudo` or as root
* You must then move the `switch_tester` directory to your home directory with `mv switch_tester/ ~/switch_tester`
	* This must be done because of assumptions made on part of OFTest
