#! /usr/bin/python3
from pyln.client import LightningRpc, RpcError
from bootstrap import rpc_decode, rpc_fetchinvoice, rpc_fetchinvoice_recurring, rpc_status
import flask
import os
import sys


sys.path.insert(0, '/home/rusty/bolt12.org/wsgi/bootstrap.wsgi')


application = flask.Flask('bootstrap')
rpc = LightningRpc('/home/rusty/.lightning/bitcoin/lightning-rpc')


@application.errorhandler(RpcError)
def handle_rpcerror(e):
    return ('Bad request: {} returned {}'.format(e.method, e.error),
            400)


@application.route('/decode/<bolt12>', methods=['GET'])
def decode(bolt12):
    return rpc_decode(rpc, bolt12)


@application.route('/fetchinvoice/<path:omq>', methods=['POST'])
def fetchinvoice(omq):
    return rpc_fetchinvoice(rpc, omq)


@application.route('/fetchinvoicerecurring/<offer>/<payerkey>/<path:counterstart>',
           methods=['POST'])
def fetchinvoice_recurring(offer, payerkey, counterstart):
    return rpc_fetchinvoice_recurring(rpc, offer, payerkey, counterstart)


@application.route('/status')
def status():
    return rpc_status(rpc)

