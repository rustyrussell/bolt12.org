#!/usr/bin/env python3
# LICENSE: MIT / APACHE
from pyln.client import RpcError, LightningRpc
from markupsafe import escape


def take_first_or_none(l):
    if len(l) == 0:
        return None
    v = l.pop(0)
    if v == '':
        return None
    return v


def rpc_decode(rpc, bolt12):
    return rpc.decode(bolt12)


def rpc_fetchinvoice(rpc, omq):
    argdict = {}
    args = escape(omq).split('/')

    argdict['offer'] = take_first_or_none(args)
    if argdict['offer'] is None:
        return ('Bad request: needs offer arg: '
                '/offer/[[msatsoshi/]quantity/]', 400)

    argdict['msatoshi'] = take_first_or_none(args)
    argdict['quantity'] = take_first_or_none(args)
    if len(args) != 0:
        return ('Bad request: only takes 1-3 params: '
                '/offer/[[msatsoshi/]quantity/]', 400)

    inv = rpc.call('fetchinvoice', argdict)
    # Save them the round trip
    inv['decoded'] = rpc.decode(inv['invoice'])
    return inv


def rpc_fetchinvoice_recurring(rpc, offer, payerkey, counterstart):
    argdict = {'offer': offer,
               'payer_secret': payerkey}
    args = escape(counterstart).split('/')

    argdict['recurrence_counter'] = take_first_or_none(args)
    if argdict['offer'] is None:
        return ('Bad request: needs counter arg: '
                ' /offer/payerkey/counter/[start]/', 400)
    argdict['recurrence_start'] = take_first_or_none(args)
    if len(args) != 0:
        return ('Bad request: only takes 3 or 4 params:'
                ' /offer/payerkey/counter/[start]/', 400)

    inv = rpc.call('fetchinvoice', argdict)
    # Save them the round trip
    inv['decoded'] = rpc.decode(inv['invoice'])
    return inv


def rpc_status(rpc):
    return rpc.getinfo()

