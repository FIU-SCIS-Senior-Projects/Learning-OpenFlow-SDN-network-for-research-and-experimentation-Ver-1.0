"""
topo-sample.py: Host subclass that uses a VLAN tag for the default interface
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
        sudo mn --custom topo-sample.py --topo=sample
"""

from mininet.node import Host
from mininet.topo import Topo

class VLANHost( Host ):
	"Host connected to VLAN interface(s)"
	
	def config( self, hostid, vlans=None, **params ):
		"""Configure VLANHost according to parameters:
		   hostid: The datapath ID for the host, used for IP configuration
		   vlans (optional): VLAN IDs for default interface"""
		
		r = super( VLANHost, self ).config( **params )
		
		intf = self.defaultIntf()
		self.setIP( '10.10.0.%d/24' % ( hostid ) )
		
		for vlan in vlans:
			vname = '%s.%d' % ( intf, vlan )
			self.cmd( 'ip link add link %s name %s type vlan id %d' % ( intf, vname, vlan ) )
			self.cmd( 'ip addr add 10.10.%d.%d/24 brd 10.10.0.255 dev %s' % ( vlan, hostid, vname ) )
			self.cmd( 'ip link set dev %s up' % ( vname ) )
	
		return r

hosts = { 'vlan': VLANHost }

class VLANSampleTopo( Topo ):
	"""
	   Sample topology that uses hosts in multiple VLANs connected to a network of switches.
	
	   Visual:
	      hE                 hA
	        \               /
	        swE --------- swA
	         | \           |
	         |   \         |
	         |     \       |
	        swD -- swC -- swB
	        /       |       \
	      hD       hC       hB
	   
	   VLANs:
	     10: hA, hB
	     20: hA, hC
	     30: hB, hC
	     40: hC, hD
	     50: hC, hE
	     60: hD, hE
	     70: hE, hA
	"""
	
	# sample topology
	def __init__( self ):
		Topo.__init__( self )
	
		# Add switches
		# NOTE: Naming convention seems to require numbers at the end of switch names.
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
		hE = self.addHost( 'hE', cls=VLANHost, hostid=5, vlans=[ 50, 60, 70 ] )
	
		# Add host links
		self.addLink( hA, swA )
		self.addLink( hB, swB )
		self.addLink( hC, swC )
		self.addLink( hD, swD )
		self.addLink( hE, swE )

topos = { 'sample' : ( lambda: VLANSampleTopo() ) }
