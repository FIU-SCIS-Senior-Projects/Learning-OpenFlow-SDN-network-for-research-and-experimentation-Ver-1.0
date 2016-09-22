"""
topo-amlight.py: Host subclass that uses a VLAN tag for the default interface
    to recreate amlight topology.

Resources:
    ArchLinux Wiki on setting up a VLAN.
    Mininet sample of custom topology (two host/switch example)
    Mininet sample of VLANHost
    Mininet tutorial on Setting Performance Parameters
    AmLight topology @ http://amlight.net/wp-content/uploads/2016/06/AMLIGHTLinks-100G-20160815.pdf

Dependencies:
    This class depends on the "vlan" package
    $ sudo apt-get install vlan

Usage:
    From the command line:
        sudo mn --custom topo-amlight.py --topo=amlight
"""

from mininet.node import Host
from mininet.topo import Topo
from mininet.link import TCLink

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

class AmLightTopo( Topo ):
	"""
	   AmLight topology that uses hosts with potentially multiple VLANs connected to a network of switches.
	
	   Visual of switch network (w/ link bandwidth):

	           10Gbps                 10Gbps
	     |------------- Fortaleza -------------|
	     |     10Gbps                 10Gbps   |
	     |------------- Santiago  -------------|
	     |     10Gbps                          |
	     |-------------------------------------|
	     |     10Gbps                          |
	     |-------------------------------------|
	     |    100Gbps                          |
	     |-------------------------------------|
	     |    100Gbps                          |
	   Miami ----------------------------- Sao Paolo
	"""
	
	def __init__( self ):
		Topo.__init__( self )
	
		# Add switches
		# NOTE: Naming convention seems to require numbers at the end of switch names.
		swMia = self.addSwitch( 'sw1' )
		swFor = self.addSwitch( 'sw2' )
		swSan = self.addSwitch( 'sw3' )
		swSao = self.addSwitch( 'sw4' )
	
		# Add switch links
		# NOTE: Bandwidth (bw) is in Mbps
		self.addLink( swMia, swFor, bw= 10000 )
		self.addLink( swMia, swSan, bw= 10000 )
		self.addLink( swMia, swSao, bw= 10000 )
		self.addLink( swMia, swSao, bw= 10000 )
		self.addLink( swMia, swSao, bw=100000 )
		self.addLink( swMia, swSao, bw=100000 )
		self.addLink( swFor, swSao, bw= 10000 )
		self.addLink( swSan, swSao, bw= 10000 )
	
		# Add hosts 
		hMia = self.addHost( 'hMia', cls=VLANHost, hostid=1 )
		hFor = self.addHost( 'hFor', cls=VLANHost, hostid=2 )
		hSan = self.addHost( 'hSan', cls=VLANHost, hostid=3 )
		hSao = self.addHost( 'hSao', cls=VLANHost, hostid=4 )
	
		# Add host links
		self.addLink( hMia, swMia )
		self.addLink( hFor, swFor )
		self.addLink( hSan, swSan )
		self.addLink( hSao, swSao )

topos = { 'amlight' : ( lambda: AmLightTopo() ) }
