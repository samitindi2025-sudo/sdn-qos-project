from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib.packet import packet, ethernet
import socket
import threading


class QoSController(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}

        thread = threading.Thread(
            target=self.control_listener,
            daemon=True
        )
        thread.start()

    def control_listener(self):

        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(("127.0.0.1", 9000))

        print("Dynamic SDN control listening on UDP 9000")

        while True:

            data, addr = server.recvfrom(1024)
            message = data.decode().strip()

            print("SDN EVENT:", message)

            if message == "CONGESTION":

                print("ACTION: Increasing HIGH traffic priority")

                for datapath in self.datapaths.values():
                    self.install_dynamic_high_priority(datapath)

            elif message == "RECOVERY":

                print("ACTION: Restoring normal QoS priorities")

                for datapath in self.datapaths.values():
                    self.remove_dynamic_high_priority(datapath)

    def remove_dynamic_high_priority(self, datapath):

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        match = parser.OFPMatch(
            in_port=1,
            eth_type=0x0800,
            ip_proto=17,
            ipv4_dst="10.0.0.2",
            udp_dst=5001
        )

        mod = parser.OFPFlowMod(
            datapath=datapath,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            priority=200,
            match=match
        )

        datapath.send_msg(mod)
        print("Dynamic rule removed: HIGH UDP 5001 h1 -> h2")

    def install_dynamic_high_priority(self, datapath):

        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
            in_port=1,
            eth_type=0x0800,
            ip_proto=17,
            ipv4_dst="10.0.0.2",
            udp_dst=5001
        )

        actions = [
            parser.OFPActionOutput(2)
        ]

        self.add_flow(
            datapath,
            200,
            match,
            actions
        )

        print(
            "Dynamic rule installed:",
            "HIGH UDP 5001",
            "h1 -> h2",
            "priority 200"
        )

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath

        print("Switch connected:", datapath.id)

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(datapath, 0, match, actions)

        self.install_qos_rules(datapath)

    def install_qos_rules(self, datapath):

        parser = datapath.ofproto_parser

        hosts = {
            1: "10.0.0.1",
            2: "10.0.0.2",
            3: "10.0.0.3"
        }

        traffic_classes = {
            5001: ("HIGH", 100),
            5002: ("MEDIUM", 50),
            5003: ("LOW", 10)
        }

        for udp_port, (traffic_class, priority) in traffic_classes.items():

            for in_port in hosts:

                for out_port in hosts:

                    if in_port == out_port:
                        continue

                    match = parser.OFPMatch(
                        in_port=in_port,
                        eth_type=0x0800,
                        ip_proto=17,
                        ipv4_dst=hosts[out_port],
                        udp_dst=udp_port
                    )

                    actions = [
                        parser.OFPActionOutput(out_port)
                    ]

                    self.add_flow(
                        datapath,
                        priority,
                        match,
                        actions
                    )

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        src = eth.src
        dst = eth.dst
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        out_port = self.mac_to_port[dpid].get(
            dst,
            ofproto.OFPP_FLOOD
        )

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst
            )

            self.add_flow(
                datapath,
                1,
                match,
                actions
            )

        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions):

        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions
        )

        datapath.send_msg(mod)
