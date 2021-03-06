#
# note: in order to use these macros we must add some mine_functions:
#       network.default_route, network.interfaces
#

from __future__ import absolute_import
from salt.ext.six import iteritems


DEFAULT_INTERFACE = 'eth0'

NODENAME_GRAIN = 'nodename'


def __virtual__():
    return "caasp_net"


def get_hosts():
    """Wrapper around hosts.list_hosts that strips useless lines.
    hosts.list_hosts includes comments as hosts - this function strips those out.
    :return: Dict(ip_address -> [aliases])
    """
    hosts = __salt__['hosts.list_hosts']()  # type: dict
    # Python3 (correctly) prevents modifying a dictionary we are iterating
    # over, so we have to copy it first, so we can remove comment entries.
    return {k: v for k, v in hosts.items() if not k.startswith("comment-")}


def get_aliases(hostname):
    """Return the aliases for the given hostname
    :param nodename:
    :return: [string]
    """
    hosts = get_hosts()
    found_aliases = set([hostname])
    for host, aliases in iteritems(hosts):
        if hostname in aliases:
            found_aliases.update(set(aliases))
    __utils__['caasp_log.debug']('CaaS: retrieved aliases %s for %s', aliases, hostname)
    return found_aliases


def get_iface_ip(iface, host=None, ifaces=None):
    '''
    given an 'iface' (and an optional 'host' and list of 'ifaces'),
    return the IP address associated with 'iface'
    '''
    try:
        if not ifaces:
            if not host or host == get_nodename():
                ifaces = __salt__['network.interfaces']()
            else:
                ifaces = __salt__['caasp_grains.get'](host, 'network.interfaces', type='glob')

        iface = ifaces.get(iface)
        ipv4addr = iface.get('inet', [{}])
        return ipv4addr[0].get('address')
    except Exception as e:
        __utils__['caasp_log.error']('could not get IP for interface %s: %s', iface, e)
        return ''


def get_primary_iface(host=None):
    '''
    (given some optional 'host')
    return the name of the primary iface (the iface associated with the default route)
    '''
    try:
        if not host or host == get_nodename():
            default_route_lst = __salt__['network.default_route']()
            return default_route_lst[0]['interface']
        else:
            all_routes = __salt__['caasp_grains.get'](host, 'network.default_route', type='glob')
            return all_routes[host][0]['interface']
    except Exception as e:
        __utils__['caasp_log.error']('could not get the primary interface: %s', e)
        return __salt__['caasp_pillar.get']('hw:netiface', DEFAULT_INTERFACE)


def get_primary_ip(host=None, ifaces=None):
    '''
    (given an optional minion 'host' and a list of its network interfaces, 'ifaces'),
    return the primary IP
    '''
    return get_iface_ip(iface=get_primary_iface(host=host), host=host, ifaces=ifaces)


def get_primary_ips_for(compound, **kwargs):
    '''
    given a compound expression 'compound', return the primary IPs for all the
    nodes that match that expression
    '''
    try:
        all_ifaces = __salt__['caasp_grains.get'](compound, 'network.interfaces')
        return [get_primary_ip(host=host, **kwargs) for host in all_ifaces.keys()]
    except Exception as e:
        __utils__['caasp_log.error']('could not get primary IPs for %s: %s', compound, e)
        return []


def get_primary_net(host=None):
    '''
    (given some optional 'host')
    return the primary network
    '''
    primary_net = __salt__['network.subnets'](get_primary_iface(host=host))
    return primary_net[0]


def get_nodename(host=None, **kwargs):
    '''
    (given some optional 'host')
    return the `nodename`
    '''
    try:
        if not host:
            assert __opts__['__role'] != 'master'
            return __salt__['grains.get'](NODENAME_GRAIN)
        else:
            all_nodenames = __salt__['caasp_grains.get'](host, grain=NODENAME_GRAIN, type='glob')
            return all_nodenames[host]
    except Exception as e:
        __utils__['caasp_log.error']('could not get nodename: %s', e)
        return ''