# Learning-OpenFlow-SDN-network-for-research-and-experimentation-Ver-1.0

### SwitchTester
SwitchTester is an application that is used to validate OpenFlow switches.
Many vendors that offer products don't fully conform to the OpenFlow specifications
as it is very new, cutting-edge technology.
Because of this, we need a way to be able to validate switches offered by many different
vendors in an automated, easy-to-use manner.
Output from existing switch validation software such as OFTest and Ryu are very verbose
and cumbersome to scan and interpret.
As such, SwitchTester provides an abstraction over the testing framework, allowing
for a common CLI, configuration, and human-readable JSON and CSV reports, and
component-based system to which new switch validation software can be added.
