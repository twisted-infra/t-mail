from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.defer import Deferred
from twisted.internet.address import IPv6Address, IPv4Address
from twisted.python.components import proxyForInterface
from twisted.mail.smtp import IMessageDelivery, SMTPServerError
from twisted.internet.endpoints import connectProtocol, clientFromString
from twisted.python import log


class _GreylistProtocol(LineOnlyReceiver, object):
    delimiter = '\n'

    def __init__(self, deferred, command):
        self.deferred = deferred
        self.command = command

    def connectionMade(self):
        self.sendLine(self.command)

    def lineReceived(self, line):
        d, self.deferred = self.deferred, None
        d.deferred.callback(line)
        self.transport.loseConnection()


def greylistCommand(command, port='unix:/var/run/greylistd/socket', reactor=None):
    if not reactor:
        from twisted.internet import reactor
    deferred = Deferred()
    d = connectProtocol(clientFromString(reactor, port), _GreylistProtocol(deferred, command))
    d.addErrback(deferred.errback)
    return deferred



class GreylistDeliveryWrapper(
        proxyForInterface(IMessageDelivery, '_delivery'), object):

    def validateTo(self, user):
        peer = user.protocol.transport.getPeer()
        if not (isinstance(peer, IPv4Address) 
                or isinstance(peer, IPv6Address)):
            # Not connected over TCP, so don't try greylisting
            return self._delivery.validateTo(user)

        command = ("IS_DEFERRED %(senderHost)s "
                   "%(senderAddress)s %(localAddress)s\n" % {
                       'senderHost': peer.host,
                       'senderAddress': str(user.orig),
                       'localAddress': str(user.destination)
                       })
        d = greylistCommand(command)

        def cbGreylist(line):
            if line == 'yes':
                raise SMTPServerError(450, "Greylisted")
            return self._delivery.validateTo(user)

        def ebGreylist(res):
            log.err(res, "Error connecting to greylist, deferring.")
            raise SMTPServerError(450, "Greylisted")

        d.addCallbacks(cbGreylist, ebGreylist)

        return d
