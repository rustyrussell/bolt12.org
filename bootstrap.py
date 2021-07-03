#!/usr/bin/env python3
# LICENSE: MIT / APACHE
from pyln.client import Plugin, RpcError, LightningRpc
import flask
import multiprocessing
import logging
from markupsafe import escape

# This makes sure flask can marshall Millisatoshi values.
class MsatJSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        try:
            return o.to_json()
        except NameError:
            pass
        return __super__.default(self, o)


flask.Flask.json_encoder = MsatJSONEncoder
app = flask.Flask('bootstrap')
plugin = Plugin()


@app.errorhandler(RpcError)
def handle_rpcerror(e):
    return ('Bad request: {} returned code {}: {}'.format(e.method,
                                                          e.error['code'],
                                                          e.error['message']),
            400)


@app.route('/decode/<bolt12>', methods=['GET'])
def decode(bolt12):
    return plugin.rpc.decode(bolt12)


def take_first_or_none(l):
    if len(l) == 0:
        return None
    return l.pop(0)


@app.route('/fetchinvoice/<path:omq>', methods=['GET'])
def fetchinvoice(omq):
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

    inv = plugin.rpc.call('fetchinvoice', argdict)
    # Save them the round trip
    inv['decoded'] = plugin.rpc.decode(inv['invoice'])
    return inv


@app.route('/fetchinvoicerecurring/<offer>/<payerkey>/<path:counterstart>',
           methods=['GET'])
def fetchinvoice_recurring(offer, payerkey, counterstart):
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

    inv = plugin.rpc.call('fetchinvoice', argdict)
    # Save them the round trip
    inv['decoded'] = plugin.rpc.decode(inv['invoice'])
    return inv


@app.route('/status')
def status():
    return plugin.rpc.getinfo()


@app.route('/')
def default_page():
    return flask.render_template('index.html',
                                 API=flask.request.base_url, NETWORK=network)


# This is stolen entirely from Rene Pickhardt's donations plugin:
# https://github.com/lightningd/plugins/tree/master/donations
def flask_process(port, app, net):
    global network
    network = net
    app.run(host="0.0.0.0", port=port)


@plugin.init()
def init(options, configuration, plugin):
    logging.basicConfig(filename=options['bootstrap-log-file'], level=logging.DEBUG)

    network = plugin.rpc.getinfo()['network']
    port = int(options['bootstrap-api-port'])
    p = multiprocessing.Process(target=flask_process,
                                args=[port, app, network],
                                name="server on port {}".format(port))
    p.start()


plugin.add_option(
    'bootstrap-api-port',
    '5000',
    'Which port should the bootstrap server listen to?'
)
plugin.add_option(
    'bootstrap-log-file',
    '/tmp/bootstrap.log',
    'Where should logs go?'
)

plugin.run()
