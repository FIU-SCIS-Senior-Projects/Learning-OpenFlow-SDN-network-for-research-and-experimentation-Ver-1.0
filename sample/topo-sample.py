"""
topo-sample1.py: Host subclass that uses a VLAN tag for the default interface
    to recreate sample topology.

Resources:
    ArchLinux Wiki on setting up a VLAN.
    Mininet sample of custom topology (two host/switch example)
    Mininet sample of VLANHost

Dependencies:
    This class depends on the "vlan" package
    $ sudo apt-get install vlan

Usage:
    From the command line:
        sudo mn --custom topo-sample1.py --topo=mytopo
"""

from mininet.node import Host
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.log import error

class VLANHost( Host ):
    "Host connected to VLAN interface(s)"

    def config( self, hostid, vlans=None, **params ):
        """Configure VLANHost according to (optional) parameters:
           vlan: VLAN ID for default interface"""

        r = super( VLANHost, self ).config( **params )

        intf = self.defaultIntf()
	self.id = hostid
	self.setIP( '10.10.0.%d' % ( hostid ) )

	for vlan in vlans:
		vname = '%s.%d' % ( intf, vlan )
		self.cmd( 'ip link add link %s name %s type vlan id %d' % ( intf, vname, vlan ) )
		self.cmd( 'ip addr add 10.10.%d.%d/24 brd 10.10.0.255 dev %s' % ( vlan, hostid, vname ) )
		self.cmd( 'ip link set dev %s up' % ( vname ) )
		# not sure if this is enough to add intf to host
		#self.nameToIntf[ vname ] =  None #self.intf( vname )

        return r

hosts = { 'vlan': VLANHost }

class VLANSampleTopo( Topo ):
    """Sample topology that uses hosts in multiple VLANs

       The topology has a 5 switches. There are multiple VLANs with
       usually 2 hosts in each, all connected in a loop. """

# sample topology
    def __init__( self ):
	Topo.__init__( self )

	# Add switches
	swA = self.addSwitch( 'sw1' )
	swB = self.addSwitch( 'sw2' )
	swC = self.addSwitch( 'sw3' )
	swD = self.addSwitch( 'sw4' )
	swE = self.addSwitch( 'sw5' )

	# Add switch links
	self.addLink( swA, swB )
	self.addLink( swB, swC )
	self.addLink( swC, swD )
	self.addLink( swD, swE )
	self.addLink( swE, swA )
	self.addLink( swE, swC )

        # Add hosts 
	hA = self.addHost( 'hA', cls=VLANHost, hostid=1, vlans=[ 10, 20, 70 ] )
	hB = self.addHost( 'hB', cls=VLANHost, hostid=2, vlans=[ 10, 30 ] )
	hC = self.addHost( 'hC', cls=VLANHost, hostid=3, vlans=[ 20, 30, 40, 50 ] )
	hD = self.addHost( 'hD', cls=VLANHost, hostid=4, vlans=[ 40, 60 ] )
	hE = self.addHost( 'hE', cls=VLANHost, hostid=5, vlans=[ 50, 60 ] )

        # Add host links
	self.addLink( hA, swA )
	self.addLink( hB, swB )
	self.addLink( hC, swC )
	self.addLink( hD, swD )
	self.addLink( hE, swE )

topos = { 'mytopo' : ( lambda: VLANSampleTopo() ) }

"""
if __name__ == '__main__':
    import sys
    from functools import partial

    from mininet.net import Mininet
    from mininet.cli import CLI
    from mininet.topo import SingleSwitchTopo
    from mininet.log import setLogLevel

    setLogLevel( 'info' )

    if not quietRun( 'which vconfig' ):
        error( "Cannot find command 'vconfig'\nThe package",
               "'vlan' is required in Ubuntu or Debian,",
               "or 'vconfig' in Fedora\n" )
        exit()

    net = Mininet( topo=VLANSampleTopo() )
    net.start()
    CLI( net )
    net.stop()
"""
