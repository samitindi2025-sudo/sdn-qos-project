from mininet.topo import Topo


class QosTopo(Topo):

    def build(self):

        # OpenFlow 1.3 switch
        s1 = self.addSwitch('s1', protocols='OpenFlow13')

        # Three hosts representing traffic classes
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')

        # Connect hosts to switch
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)


topos = {
    'qos': QosTopo
}
