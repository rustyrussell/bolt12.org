#! /usr/bin/python3
from pyln.client import LightningRpc
from bootstrap import rpc_decode, rpc_fetchinvoice, rpc_fetchinvoice_recurring, rpc_status
import flask
from wsgiref.handlers import CGIHandler
import os
import sys


sys.path.insert(0, '/home/rusty/bolt12.org/wsgi/bootstrap.cgi')


app = flask.Flask('bootstrap')
rpc = LightningRpc('/home/rusty/.lightning/bitcoin/lightning-rpc')

@app.route('/decode/<bolt12>', methods=['GET'])
def decode(bolt12):
    return rpc_decode(rpc, bolt12)


@app.route('/fetchinvoice/<path:omq>', methods=['POST'])
def fetchinvoice(omq):
    return rpc_fetchinvoice(rpc, omq)


@app.route('/fetchinvoicerecurring/<offer>/<payerkey>/<path:counterstart>',
           methods=['POST'])
def fetchinvoice_recurring(offer, payerkey, counterstart):
    return rpc_fetchinvoice_recurring(rpc, offer, payerkey, counterstart)


@app.route('/status')
def status():
    return rpc_status(rpc)


CGIHandler().run(app)

