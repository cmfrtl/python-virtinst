#
# Copyright 2009  Red Hat, Inc.
# Cole Robinson <crobinso@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free  Software Foundation; either version 2 of the License, or
# (at your option)  any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA.

import libxml2
import libvirt
from virtinst import _virtinst as _

# class USBDevice

CAPABILITY_TYPE_SYSTEM = "system"
CAPABILITY_TYPE_NET = "net"
CAPABILITY_TYPE_PCI = "pci"
CAPABILITY_TYPE_USBDEV = "usb_device"
CAPABILITY_TYPE_USBBUS = "usb"
CAPABILITY_TYPE_STORAGE = "storage"
CAPABILITY_TYPE_SCSIBUS = "scsi_host"
CAPABILITY_TYPE_SCSIDEV = "scsi"

class NodeDevice(object):
    def __init__(self, node):
        self.name = None
        self.parent = None
        self.device_type = None

        self._parseNodeXML(node)


    def _parseNodeXML(self, node):
        child = node.children
        while child:
            if child.name == "name":
                self.name = child.content
            elif child.name == "parent":
                self.parent = child.content
            elif child.name == "capability":
                self.device_type = child.prop("type")
            child = child.next

    def _getCapabilityNode(self, node):
        child = node.children
        while child:
            if child.name == "capability":
                return child
            child = child.next
        return None

    def _parseValueHelper(self, node, value_map):
        if value_map.has_key(node.name):
            setattr(self, value_map[node.name], node.content)

    def _parseHelper(self, main_node, value_map):
        node = main_node.children
        while node:
            self._parseValueHelper(node, value_map)
            node = node.next

class SystemDevice(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.hw_vendor = None
        self.hw_version = None
        self.hw_serial = None
        self.hw_uuid = None

        self.fw_vendor = None
        self.fw_version = None
        self.fw_date = None

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        child = node.children
        hardware_map = {"vendor": "hw_vendor",
                        "version": "hw_version",
                        "serial": "hw_serial",
                        "uuid": "hw_uuid"}
        firmware_map = {"vendor": "fw_vendor",
                        "version": "fw_version",
                        "release_date": "fw_date" }
        while child:
            if child.name == "hardware":
                self._parseHelper(child, hardware_map)
            elif child.name == "firmware":
                self._parseHelper(child, firmware_map)
            child = child.next

class NetDevice(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.interface = None
        self.address = None
        self.capability_type = None

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        value_map = { "interface" : "interface",
                      "address" : "address", }
        child = node.children
        while child:
            if child.name == "capability":
                self.capability_type = child.prop("type")
            else:
                self._parseValueHelper(child, value_map)
            child = child.next

class PCIDevice(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.domain = None
        self.bus = None
        self.slot = None
        self.function = None

        self.product_id = None
        self.product_name = None
        self.vendor_id = None
        self.vendor_name = None

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        val_map = { "domain" : "domain",
                    "bus" : "bus",
                    "slot" : "slot",
                    "function" : "function" }
        child = node.children
        while child:
            if child.name == "vendor":
                self.vendor_name = child.content
                self.vendor_id = child.prop("id")

            elif child.name == "product":
                self.product_name = child.content
                self.product_id = child.prop("id")

            else:
                self._parseValueHelper(child, val_map)

            child = child.next

class USBDevice(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.bus = None
        self.device = None

        self.product_id = None
        self.product_name = None
        self.vendor_id = None
        self.vendor_name = None

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        val_map = { "bus": "bus", "device": "device"}
        child = node.children
        while child:
            if child.name == "vendor":
                self.vendor_name = child.content
                self.vendor_id = child.prop("id")

            elif child.name == "product":
                self.product_name = child.content
                self.product_id = child.prop("id")

            else:
                self._parseValueHelper(child, val_map)

            child = child.next

class StorageDevice(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.block = None
        self.bus = None
        # FIXME: Map this to virtinst.device?
        self.drive_type = None
        self.size = 0

        self.model = None
        self.vendor = None

        self.removable = False
        self.media_available = False
        self.media_size = 0

        self.hotpluggable = False

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        val_map = { "block" : "block",
                    "bus" : "bus",
                    "drive_type" : "drive_type",
                    "model" : "model",
                    "vendor" : "vendor"}
        child = node.children
        while child:
            if child.name == "size":
                self.size = int(child.content)
            elif child.name == "capability":

                captype = child.prop("type")
                if captype == "hotpluggable":
                    self.hotpluggable = True
                elif captype == "removable":
                    self.removable = True
                    rmchild = child.children
                    while rmchild:
                        if rmchild.name == "media_available":
                            self.media_available = bool(int(rmchild.content))
                        elif rmchild.name == "media_size":
                            self.media_size = int(rmchild.content)
                        rmchild = rmchild.next
            else:
                self._parseValueHelper(child, val_map)

            child = child.next

class USBBus(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.number = None
        self.classval = None
        self.subclass = None
        self.protocol = None

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        val_map = { "number" : "number",
                    "class" : "classval",
                    "subclass" : "subclass",
                    "protocol" : "protocol" }
        self._parseHelper(node, val_map)

class SCSIDevice(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.host = None
        self.bus = None
        self.target = None
        self.lun = None
        self.disk = None

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        val_map = { "host" : "host",
                    "bus" : "bus",
                    "target": "target",
                    "lun" : "lun",
                    "type" : "type"}
        self._parseHelper(node, val_map)

class SCSIBus(NodeDevice):
    def __init__(self, node):
        NodeDevice.__init__(self, node)

        self.host = None

        self.parseXML(self._getCapabilityNode(node))

    def parseXML(self, node):
        val_map = { "host" : "host" }
        self._parseHelper(node, val_map)


def is_nodedev_capable(conn):
    """
    Check if the passed libvirt connection supports host device routines

    @param conn: Connection to check
    @type conn: libvirt.virConnect

    @rtype: C{bool}
    """
    if not conn:
        return False
    if not isinstance(conn, libvirt.virConnect):
        raise ValueError(_("'conn' must be a virConnect instance."))

    if dir(libvirt).count("virNodeDevice") == 0:
        # Local libvirt doesn't support it
        return False

    try:
        conn.listDevices(None, 0)
        return True
    except Exception, e:
        if (e.get_error_code() == libvirt.VIR_ERR_RPC or
            e.get_error_code() == libvirt.VIR_ERR_NO_SUPPORT):
            return False

    return True

def is_pci_detach_capable(conn):
    """
    Check if the passed libvirt connection support pci device Detach/Reset

    @param conn: Connection to check
    @type conn: libvirt.virConnect

    @rtype: C{bool}
    """
    if not conn:
        return False
    if not isinstance(conn, libvirt.virConnect):
        raise ValueError(_("'conn' must be a virConnect instance."))

    if dir(libvirt).count("virNodeDeviceDettach") == 0:
        return False

    return True

def lookupNodeName(conn, name):
    """
    Convert the passed libvirt node device name to a NodeDevice
    instance, with proper error reporting.

    @param conn: libvirt.virConnect instance to perform the lookup on
    @param name: libvirt node device name to lookup

    @rtype: L{NodeDevice} instance
    """

    if not is_nodedev_capable(conn):
        raise ValueError(_("Connection does not support host device "
                           "enumeration."))

    nodedev = conn.nodeDeviceLookupByName(name)
    xml = nodedev.XMLDesc(0)
    return parse(xml)


def parse(xml):
    """
    Convert the passed libvirt node device xml into a NodeDevice object

    @param xml: libvirt node device xml
    @type xml: C{str}

    @returns: L{NodeDevice} instance
    """

    class ErrorHandler:
        def __init__(self):
            self.msg = ""
        def handler(self, ignore, s):
            self.msg += s
    error = ErrorHandler()
    libxml2.registerErrorHandler(error.handler, None)

    try:
        # try/except/finally is only available in python-2.5
        try:
            doc = libxml2.readMemory(xml, len(xml),
                                     None, None,
                                     libxml2.XML_PARSE_NOBLANKS)
        except (libxml2.parserError, libxml2.treeError), e:
            raise ValueError("%s\n%s" % (e, error.msg))
    finally:
        libxml2.registerErrorHandler(None, None)

    try:
        root = doc.getRootElement()
        if root.name != "device":
            raise ValueError("Root element is not 'device'")

        t = _findNodeType(root)
        devclass = _typeToDeviceClass(t)
        device = devclass(root)
    finally:
        doc.freeDoc()

    return device

def _findNodeType(node):
    child = node.children
    while child:
        if child.name == "capability":
            return child.prop("type")
        child = child.next
    return None

def _typeToDeviceClass(t):
    if t == CAPABILITY_TYPE_SYSTEM:
        return SystemDevice
    elif t == CAPABILITY_TYPE_NET:
        return NetDevice
    elif t == CAPABILITY_TYPE_PCI:
        return PCIDevice
    elif t == CAPABILITY_TYPE_USBDEV:
        return USBDevice
    elif t == CAPABILITY_TYPE_USBBUS:
        return USBBus
    elif t == CAPABILITY_TYPE_STORAGE:
        return StorageDevice
    elif t == CAPABILITY_TYPE_SCSIBUS:
        return SCSIBus
    elif t == CAPABILITY_TYPE_SCSIDEV:
        return SCSIDevice

    raise ValueError(_("Unknown host device capability '%s'.") % t)
