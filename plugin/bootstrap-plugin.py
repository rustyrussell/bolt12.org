#!/usr/bin/env python3
# LICENSE: MIT / APACHE
from pyln.client import Plugin, RpcError, LightningRpc
from bootstrap import rpc_decode, rpc_fetchinvoice, rpc_fetchinvoice_recurring, rpc_status
import flask
import multiprocessing
import logging
import qrcode
import io
import os
import time
from markupsafe import escape


# This makes sure flask can marshall Millisatoshi values.
class MsatJSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        try:
            return o.to_json()
        except NameError:
            pass
        return __super__.default(self, o)

plugin = Plugin()
flask.Flask.json_encoder = MsatJSONEncoder
app = flask.Flask('bootstrap')

@app.route('/decode/<bolt12>', methods=['GET'])
def decode(bolt12):
    return rpc_decode(plugin.rpc, bolt12)


@app.route('/fetchinvoice/<path:omq>', methods=['POST'])
def fetchinvoice(omq):
    return rpc_fetchinvoice(plugin.rpc, omq)


@app.route('/fetchinvoicerecurring/<offer>/<payerkey>/<path:counterstart>',
           methods=['POST'])
def fetchinvoice_recurring(offer, payerkey, counterstart):
    return rpc_fetchinvoice_recurring(plugin.rpc, offer, payerkey, counterstart)


@app.route('/status')
def status():
    return rpc_status(plugin.rpc)


@app.route('/')
def default_page():
    return flask.render_template('index.html',
                                 API=flask.request.base_url, NETWORK=network)


@app.route('/examples')
def example_page():
    # You can generate the examples for your own node, as so:
    # sed -n 's,Created by.*<tt>\(.*\)</tt>,\1,pg' < templates/examples.html | while read CMD; do eval $CMD > /tmp/out.json; echo '{ "offer": '$(jq .offer_id < /tmp/out.json)","; echo ' "bolt12": '$(jq .bolt12 < /tmp/out.json)' },'; done
    if network == "regtest":
        examples=[
{ "offer": "035d8cfeb1a08b2e86b516c176c5acfc3ffc001b8942e3e7c4b6030b43b86b30",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2z48kven9wgsxy7fqwf6hxareyaejqmn0v3j3vggz6enkl90qe98lmfwczz3q2jrr08sgxjjp8jjsr9rmmlmk7f8uqktq" },
{ "offer": "032810f1d436b976bbdc444381330104ac92bae5ab4bc601f4eff3e964de80ea",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqyeq5xe4xpkhxct5ypkh2mr5dykhzatpde6xjareyphkven9wgfq7un4wd6xxmmjwqhxxmmd9esh29qqzcss94n8d727pj20lkjasy9zq4yxx70qsd9yz099qx28hhlhduj0cpvk" },
{ "offer": "c02bb1449b3465999af5aad46793d3450f3b9164384bef4110a45260cd1a8d50",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq59p3xqcx6umpwssx2an9wfujqmtfde6hgegjzpe82um50yhx77nvv938xtn0wfn3vggz6enkl90qe98lmfwczz3q2jrr08sgxjjp8jjsr9rmmlmk7f8uqktp5qsq8s" },
{ "offer": "c63de24024f6428a84ada2634e0e99c56fb2f97d53bd0b1d3b1b12e4ac70e466",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq5fe3xqcx6umpwssx2an9wfujqmtfde6hgefvyp6hqgr5dus8g6rjv4jjqarfd4jhxysswf6hxare9ehh5mrpvfejummjvutzzqkkvahetcxffl76tkqs5gz5scmeuzp55sfu55qeg77l7ahjflq9jcdqyqpurcqsy" },
{ "offer": "9ec2f7cf320deffb08a7418d9044f237fa2e0682760ad941e1d7c4faf3009a1f",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq5g33xqcx6umpwssx2an9wfujqerp0ykzqenjdakjqvfdffskutfjxqerzysswf6hxare9ehh5mrpvfejummjvutzzqkkvahetcxffl76tkqs5gz5scmeuzp55sfu55qeg77l7ahjflq9jcdqyqgpyqzszhld6fvq" },
{ "offer": "5fceabb3b5edd486b12bdef1421e3bf0e3fc4e480252c5d3dea31906909d2e11",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqgp7szj2xycrqvrdwdshggr9wejhy7fqxyczqerp09ejcgrxwfhk6gp3949xzm3dxgcryvfvypcxz7fqx958ygrzv4nx7un9yp6x7gpkxqs8xetrdahxgueqd3shgegjzpe82um50yhx77nvv938xtn0wfn3vggz6enkl90qe98lmfwczz3q2jrr08sgxjjp8jjsr9rmmlmk7f8uqktp5qsppgwqvqqqpcgqq0pqq5q4lmwjtq" },
{ "offer": "0072b2f3228305ddade994ac9f1e84e4a08172c418fd69b8e38d1f70b02cd1fb",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqgp7sz33xycrqvrdwdshggr9wejhy7fqxyczqerp09ejcgrxwfhk6gp3949xzm3dxgcryvfvypc8ymedwfshgcgjzpe82um50yhx77nvv938xtn0wfn3vggz6enkl90qe98lmfwczz3q2jrr08sgxjjp8jjsr9rmmlmk7f8uqktp5qsppgwqsqqd9uqqzrf0qqsq2q2lahf9s" },
{ "offer": "7a046e81f1929604a06b4c799623974283318eb3ff00638ecb177b0b2c2d45d8",
 "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcxqd24x3qgqgp7szs0xyc9256yypjhvetj0ysxgctezgg8yatnw3ujumm6d3skyuewdaexw93pqttxwmu4ury5lld9mqg2yp2gvdu7pq62gy722qv5000lwmeylszevxszqyqs" },
    elif network == 'bitcoin':
        examples=[
            { "offer": "826eecb3a346de937e38d1bb57b7a4944f5a35174dd8b74d98e31d74fe1bef69",
              "bolt12": "lno1pg257enxv4ezqcneype82um50ynhxgrwdajx293pqglnyxw6q0hzngfdusg8umzuxe8kquuz7pjl90ldj8wadwgs0xlmc" },
            { "offer": "61f5ec52ee14a1237eba158ea3ec90d95801820f3119007ff2d7eb403182bd19",
              "bolt12": "lno1pqqnyzsmx5cx6umpwssx6atvw35j6ut4v9h8g6t50ysx7enxv4epyrmjw4ehgcm0wfczucm0d5hxzag5qqtzzq3lxgva5qlw9xsjmeqs0ek9cdj0vpec9ur972l7mywa66u3q7dlhs" },
            { "offer": "a679b33f3a2f1a7b5976685883738fac2050a2e6ee89f9663c9612c41feee4b1",
              "bolt12": "lno1pqqkgzs5xycrqmtnv96zqetkv4e8jgrdd9h82ar9zgg8yatnw3ujumm6d3skyuewdaexw93pqglnyxw6q0hzngfdusg8umzuxe8kquuz7pjl90ldj8wadwgs0xlmcxszqq7q" },
            { "offer": "c16b60d7480ccd382f0abb8260e7675f7a61f7da770fc19f636c68b858e678a7",
              "bolt12": "lno1pqqkgz38xycrqmtnv96zqetkv4e8jgrdd9h82ar99ss82upqw3hjqargwfjk2gr5d9kk2ucjzpe82um50yhx77nvv938xtn0wfn3vggz8uepnksrac56zt0yzplxchpkfas88qhsvhetlmv3mhttjyreh77p5qsq8s0qzqs" },
            { "offer": "1bd4e52419c8bcb19099d72d3ae2b69ae187b327ef105106bbca3977e9dd9d95",
              "bolt12": "lno1pqqkgz3zxycrqmtnv96zqetkv4e8jgryv9ujcgrxwfhk6gp3949xzm3dxgcryvgjzpe82um50yhx77nvv938xtn0wfn3vggz8uepnksrac56zt0yzplxchpkfas88qhsvhetlmv3mhttjyreh77p5qspqysq2q2laenqq" },
            { "offer": "b9f77229df304ae34ecee7a26ecb66e4cdfb7af54c08e89f402408ee954e76b2",
              "bolt12": "lno1pqpq86q2fgcnqvpsd4ekzapqv4mx2uneyqcnqgryv9uhxtpqveex7mfqxyk55ctw95erqv339ss8qcteyqcksu3qvfjkvmmjv5s8gmeqxcczqum9vdhkuernypkxzar9zgg8yatnw3ujumm6d3skyuewdaexw93pqglnyxw6q0hzngfdusg8umzuxe8kquuz7pjl90ldj8wadwgs0xlmcxszqy9pcpsqqq8pqqpuyqzszhlwvcqq" },
            { "offer": "496e877a7448b7b4f117a56d469e8e1dcecbab81d33cc3caa5bf722155a11e39",
              "bolt12": "lno1pqpq86q2xycnqvpsd4ekzapqv4mx2uneyqcnqgryv9uhxtpqveex7mfqxyk55ctw95erqv339ss8qun094exzarpzgg8yatnw3ujumm6d3skyuewdaexw93pqglnyxw6q0hzngfdusg8umzuxe8kquuz7pjl90ldj8wadwgs0xlmcxszqy9pczqqp5hsqqgd9uqzqpgptlhxvqq" },
            { "offer": "90c463cf49014f26a89c2792743ada87e39362ecb615b19522c38cc4672480bb",
              "bolt12": "lno1qcp4256ypqpq86q2pucnq42ngssx2an9wfujqerp0yfpqun4wd68jtn00fkxzcnn9ehhyeckyypr7vsemgp7u2dp9hjpqlnvtsmy7crnstcxtu4lakgam44ezpuml0q6qgqsz" },
        ]
    DATE_JAN1_2021 = 1609421400
    DAYS_SINCE = int((time.time() - DATE_JAN1_2021) // (60 * 60 * 24))
    return flask.render_template('examples.html',
                                 API=flask.request.base_url,
                                 NETWORK=network,
                                 EXAMPLES=examples, DAYS_SINCE=DAYS_SINCE)


# This is stolen entirely from Rene Pickhardt's donations plugin:
# https://github.com/lightningd/plugins/tree/master/donations
def flask_process(port, app, net, ssl_context):
    global network
    network = net
    app.run(host="0.0.0.0", port=port, ssl_context=ssl_context)


@plugin.init()
def init(options, configuration, plugin):
    logging.basicConfig(filename=options['bootstrap-log-file'], level=logging.DEBUG)

    network = plugin.rpc.getinfo()['network']
    port = int(options['bootstrap-api-port'])
    if options['bootstrap-ssl']:
        ssl_context = (os.getenv('HOME')
                       + '/etc/dehydrated/certs/bootstrap.bolt12.org/fullchain.pem',
                       os.getenv('HOME')
                       + '/etc/dehydrated/certs/bootstrap.bolt12.org/privkey.pem')
    else:
        ssl_context = None
        p = multiprocessing.Process(target=flask_process,
                                args=[port, app, network, ssl_context],
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
plugin.add_option(
    'bootstrap-ssl',
    'true',
    'Should we serve ssl as well?',
    'bool'
)

plugin.run()
