#!/usr/bin/env python3
# LICENSE: MIT / APACHE
from pyln.client import Plugin, RpcError, LightningRpc
import flask
import multiprocessing
import logging
import qrcode
import io
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


@app.errorhandler(RpcError)
def handle_rpcerror(e):
    return ('Bad request: {} returned {}'.format(e.method, e.error),
            400)


@app.route('/qrcode/<string>')
def draw_qrcode(string):
    img = qrcode.make(string, error_correction=qrcode.ERROR_CORRECT_L)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return flask.Response(buf.getvalue(), mimetype='image/png')


@app.route('/decode/<bolt12>', methods=['GET'])
def decode(bolt12):
    return plugin.rpc.decode(bolt12)


def take_first_or_none(l):
    if len(l) == 0:
        return None
    v = l.pop(0)
    if v == '':
        return None
    return v


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


@app.route('/examples')
def example_page():
    # You can generate the examples for your own node, as so:
    # sed -n 's,Created by.*<tt>\(.*\)</tt>,\1,pg' < templates/examples.html | while read CMD; do eval $CMD > /tmp/out.json; echo '{ "offer": '$(jq .offer_id < /tmp/out.json)","; echo ' "bolt12": '$(jq .bolt12 < /tmp/out.json)","; echo ' "bolt12_unsigned": '$(jq .bolt12_unsigned < /tmp/out.json)' },'; done
    if network == "regtest":
        examples=[
            { "offer": "8398b56cca26ca166f5c75b00942c7c2a98bfd8e008fcf511bb56dca811571f9",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2z48kven9wgsxy7fqwf6hxareyaejqmn0v3j3ugxff8l7qsrc3s9szhc62zjrljhgg0ssuq56fwsgxql3dq99609xa8cyqtyyc0jhqm2cxn69h6p9xcfcuapyswundl0pac9zk9gke9x7cgr8l78g2fxet40swguclehpu8p66vszdkaqgd7la9gr8lv6w3w7j5zs",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2z48kven9wgsxy7fqwf6hxareyaejqmn0v3j3ugxff8l7qsrc3s9szhc62zjrljhgg0ssuq56fwsgxql3dq99609xay" },
            { "offer": "36741fe3ed8b26640f6c7a4d74d215e90c5a4ee8aaf54f09053abf80faf1c64b",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqyeq5xe4xpkhxct5ypkh2mr5dykhzatpde6xjareyphkven9wg2q7un4wd6xxmmjwqhxxmmd9esh29spqy0zpj2fllsyq7yvpvq47xjs5slu46zruy8q9xjt5zps8utgpfwnefhf7pqyygmre95ttyw9e3x7n8hc2yxhmp30559ysnxfxm30nw0jxugtjzf8hf4q758jyjftw80ng9dhswhdy208zpq7gj37tewxea9mr5qxa5",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqyeq5xe4xpkhxct5ypkh2mr5dykhzatpde6xjareyphkven9wg2q7un4wd6xxmmjwqhxxmmd9esh29spqy0zpj2fllsyq7yvpvq47xjs5slu46zruy8q9xjt5zps8utgpfwnefhf" },
            { "offer": "fae0598ccc2d43ae56047278473e0bff1a42d1edf7aae0a69b5eaeb5608187dd",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq59p3xqcx6umpwssx2an9wfujqmtfde6hgeg5zpe82um50yhx77nvv938xtn0wfn35qsq8s0zpj2fllsyq7yvpvq47xjs5slu46zruy8q9xjt5zps8utgpfwnefhf7pqfw2j2d352g6c8495mpma6m90ry6rknh2ujnr65d3fmzuwatmvykcldsv4d6f6eq32rv354j8f5kyfga0qxwhwm2yzp007458eygjwns",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq59p3xqcx6umpwssx2an9wfujqmtfde6hgeg5zpe82um50yhx77nvv938xtn0wfn35qsq8s0zpj2fllsyq7yvpvq47xjs5slu46zruy8q9xjt5zps8utgpfwnefhf" },
            { "offer": "c8ff6061a285094979f34a7acdbf9e71cda36af78e9b0d84f505be224c2dc295",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq5fe3xqcx6umpwssx2an9wfujqmtfde6hgefvyp6hqgr5dus8g6rjv4jjqarfd4jhx9qswf6hxare9ehh5mrpvfejummjvudqyqpurcsvjj0lupq83rqtq903559y8l9wsslppcpf5jaqsvplz6q2t572d62zqyp0qsrpnh2k8nr5a5rtsw58mhuacrzrt8upw8n3atmgctzfqza74l5wsn5n9uwdvrxuuu2xfrfmec64e9yckc4vlwwk8tmr8rr6qs5fa9msv",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq5fe3xqcx6umpwssx2an9wfujqmtfde6hgefvyp6hqgr5dus8g6rjv4jjqarfd4jhx9qswf6hxare9ehh5mrpvfejummjvudqyqpurcsvjj0lupq83rqtq903559y8l9wsslppcpf5jaqsvplz6q2t572d62zqypq" },
            { "offer": "307b0b51c8448e5013b25b358ef5a175eb3792023eef5291a9221e7f6951480a",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq5g33xqcx6umpwssx2an9wfujqerp0ykzqenjdakjqvfdffskutfjxqerz9qswf6hxare9ehh5mrpvfejummjvudqyqgprszszhld6fvpugxff8l7qsrc3s9szhc62zjrljhgg0ssuq56fwsgxql3dq99609xa8cyq90p3923k8q3j0elas6wjy7hwsj2rju0c0vd5r3mrsfcx66z6nex99r3mwuvgkjzh5zckcsxps9hzu4ls9hgw685u5emjdqaav9fy4zq",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgq9jq5g33xqcx6umpwssx2an9wfujqerp0ykzqenjdakjqvfdffskutfjxqerz9qswf6hxare9ehh5mrpvfejummjvudqyqgprszszhld6fvpugxff8l7qsrc3s9szhc62zjrljhgg0ssuq56fwsgxql3dq99609xay" },
            { "offer": "042fd615146d1ab37e08c16f0ebadeaae97ddaf7a75642ca14d734dc85a411f7",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqgp7szj2xycrqvrdwdshggr9wejhy7fqxyczqerp09ejcgrxwfhk6gp3949xzm3dxgcryvfvypcxz7fqx958ygrzv4nx7un9yp6x7gpkxqs8xetrdahxgueqd3shgeg5zpe82um50yhx77nvv938xtn0wfn35qsppgwq2q2lahf9s83qe9yllczq0zxqkq2lrfg2g072app7zrsznf96pqcr795q5hfu5m55qpsqqq8pqqpu7pqzk4k0h4kekghe45zvv2hjrqltsehes8yeegjkcxutzj4fhrzcgrvz9cywqlklkqfuuksgat88xhhm7wmck8lvzgh46wzuh7v7uachcs",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqgp7szj2xycrqvrdwdshggr9wejhy7fqxyczqerp09ejcgrxwfhk6gp3949xzm3dxgcryvfvypcxz7fqx958ygrzv4nx7un9yp6x7gpkxqs8xetrdahxgueqd3shgeg5zpe82um50yhx77nvv938xtn0wfn35qsppgwq2q2lahf9s83qe9yllczq0zxqkq2lrfg2g072app7zrsznf96pqcr795q5hfu5m55qpsqqq8pqqpu" },
            { "offer": "2ad2806be53b33e8b3caeb29b74996b28970c8a4bbc7f57362ad77bb2a43b827",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqgp7sz33xycrqvrdwdshggr9wejhy7fqxyczqerp09ejcgrxwfhk6gp3949xzm3dxgcryvfvypc8ymedwfshgcg5zpe82um50yhx77nvv938xtn0wfn35qsppgwq2q2lahf9s83qe9yllczq0zxqkq2lrfg2g072app7zrsznf96pqcr795q5hfu5m55qzqqp5hsqqgd9uq0qsz4qa2zujg7eakv2dlk0wz0cudwpxnfnw72qn956y4v6t0mdrsjz6ehsmljjh2ezh409vs84lp4wav59auf8tk2agkn0rqa29gr7hyxv",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcgqgp7sz33xycrqvrdwdshggr9wejhy7fqxyczqerp09ejcgrxwfhk6gp3949xzm3dxgcryvfvypc8ymedwfshgcg5zpe82um50yhx77nvv938xtn0wfn35qsppgwq2q2lahf9s83qe9yllczq0zxqkq2lrfg2g072app7zrsznf96pqcr795q5hfu5m55qzqqp5hsqqgd9uqq" },
            { "offer": "2559740fb28cc23982557fa6e74ad7203a829eeb8538fed2cd39431de5b073d7",
              "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcxqd24x3qgqgp7szs0xyc9256yypjhvetj0ysxgctezsg8yatnw3ujumm6d3skyuewdaexwxszqyq3ugxff8l7qsrc3s9szhc62zjrljhgg0ssuq56fwsgxql3dq99609xa8cyqcydgst24m87jtlu3v4nwxkxr4dg9aymaxjgxwsr9mspfsayqmuaf9lz2gm6wf3clx0wj4ekyu0epu5du5lxl4xxaf6ygdm9mtpk27ms",
              "bolt12_unsigned": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrcxqd24x3qgqgp7szs0xyc9256yypjhvetj0ysxgctezsg8yatnw3ujumm6d3skyuewdaexwxszqyq3ugxff8l7qsrc3s9szhc62zjrljhgg0ssuq56fwsgxql3dq99609xay" }]
    elif network == 'bitcoin':
        examples=[
            { "offer": "28522b52ac39fa518ce3a5b3e4a9a96372487e78ba5eb1540ec4d9f02ca82718",
              "bolt12": "lno1pg257enxv4ezqcneype82um50ynhxgrwdajx283qfwdpl28qqmc78ymlvhmxcsywdk5wrjnj36jryg488qwlrnzyjczlqs85ck65ycmkdk92smwt9zuewdzfe7v4aavvaz5kgv9mkk63v3s0ge0f099kssh3yc95qztx504hu92hnx8ctzhtt08pgk0texz0509tk",
              "bolt12_unsigned": "lno1pg257enxv4ezqcneype82um50ynhxgrwdajx283qfwdpl28qqmc78ymlvhmxcsywdk5wrjnj36jryg488qwlrnzyjczs" },
            { "offer": "1cacc1f7d2b3a6b5f698069e3793f96bdcc32cfb249dde3b1d55c7f2f85c2985",
              "bolt12": "lno1pqqnyzsmx5cx6umpwssx6atvw35j6ut4v9h8g6t50ysx7enxv4epgrmjw4ehgcm0wfczucm0d5hxzagkqyq3ugztng063cqx783exlm97ekyprnd4rsu5u5w5sez9fecrhcuc3ykqhcypjju7unu05vav8yvhn27lztf46k9gqlga8uvu4uq62kpuywnu6me8srgh2q7puczukr8arectaapfl5d4rd6uc7st7tnqf0ttx39n40s",
              "bolt12_unsigned": "lno1pqqnyzsmx5cx6umpwssx6atvw35j6ut4v9h8g6t50ysx7enxv4epgrmjw4ehgcm0wfczucm0d5hxzagkqyq3ugztng063cqx783exlm97ekyprnd4rsu5u5w5sez9fecrhcuc3ykq5" },
            { "offer": "34145f989a97260e6e1e1fb835ea4e58f582d514cc3e4e91dcdde114d2130578",
              "bolt12": "lno1pqqkgzs5xycrqmtnv96zqetkv4e8jgrdd9h82ar9zsg8yatnw3ujumm6d3skyuewdaexwxszqq7pugztng063cqx783exlm97ekyprnd4rsu5u5w5sez9fecrhcuc3ykqhcyp5jq3tl57jh3g32qwfy9hpa88eqwst78gn06v9xcd485hezgs8xe2800mrth3tznd5884dnnpg3sd0tvv7k9er8ex5pg0prrnl66xd7s",
              "bolt12_unsigned": "lno1pqqkgzs5xycrqmtnv96zqetkv4e8jgrdd9h82ar9zsg8yatnw3ujumm6d3skyuewdaexwxszqq7pugztng063cqx783exlm97ekyprnd4rsu5u5w5sez9fecrhcuc3ykq5" },
            { "offer": "c1a4b907e4a95fe72c3d561f2ad33e96cbb509ca50f9fee1338f15949f3250bf",
              "bolt12": "lno1pqqkgz38xycrqmtnv96zqetkv4e8jgrdd9h82ar99ss82upqw3hjqargwfjk2gr5d9kk2uc5zpe82um50yhx77nvv938xtn0wfn35qsq8s0zqju6r75wqph3uwfh7e0kd3qgumdgu8989r4yxg32wwqa78xyf9s9ggqs9uzqd7zy5v0cehj4ev52g7ljaec4qqdmjk2lkv58z32mn5z5q8rsyp6fpqnyu2q6gcz6nvmdtmtgyzs3xxhchr09qsupd4tngtq6frkpumc",
              "bolt12_unsigned": "lno1pqqkgz38xycrqmtnv96zqetkv4e8jgrdd9h82ar99ss82upqw3hjqargwfjk2gr5d9kk2uc5zpe82um50yhx77nvv938xtn0wfn35qsq8s0zqju6r75wqph3uwfh7e0kd3qgumdgu8989r4yxg32wwqa78xyf9s9ggqsy" },
            { "offer": "bf3c613604bb741ab649f0712fa26ec8c74f06aea159714989de2095e0737f85",
              "bolt12": "lno1pqqkgz3zxycrqmtnv96zqetkv4e8jgryv9ujcgrxwfhk6gp3949xzm3dxgcryvg5zpe82um50yhx77nvv938xtn0wfn35qspqywq2q2laenqq83qfwdpl28qqmc78ymlvhmxcsywdk5wrjnj36jryg488qwlrnzyjczlqsytf0g06zjgcrtk0n09n5wk78ssdhckpmfqmfvlxm92u36egsmf3kswfpqt70dq6mg4lw3t8qx7feh6c8hxz2vwzsdg4n957z8gh8unx",
              "bolt12_unsigned": "lno1pqqkgz3zxycrqmtnv96zqetkv4e8jgryv9ujcgrxwfhk6gp3949xzm3dxgcryvg5zpe82um50yhx77nvv938xtn0wfn35qspqywq2q2laenqq83qfwdpl28qqmc78ymlvhmxcsywdk5wrjnj36jryg488qwlrnzyjczs" },
            { "offer": "37fec3bf68b1938c4f27f586edec66e9eff4e0c8fe1c752512b9e89a804fbc9a",
              "bolt12": "lno1pqpq86q2fgcnqvpsd4ekzapqv4mx2uneyqcnqgryv9uhxtpqveex7mfqxyk55ctw95erqv339ss8qcteyqcksu3qvfjkvmmjv5s8gmeqxcczqum9vdhkuernypkxzar9zsg8yatnw3ujumm6d3skyuewdaexwxszqy9pcpgptlhxvqq7yp9e58aguqr0rcun0ajlvmzq3ek63cw2w282gv3z5uupmuwvgjtq2sqxqqqquyqq8ncyph3h0xskvfd69nppz2py2nxym7rlq255z4mevv5x7vqh077n792e3gcua5p734l7d2r0x7kat69gx6c3twqexgmplmmjz2tv9hne4j5s",
              "bolt12_unsigned": "lno1pqpq86q2fgcnqvpsd4ekzapqv4mx2uneyqcnqgryv9uhxtpqveex7mfqxyk55ctw95erqv339ss8qcteyqcksu3qvfjkvmmjv5s8gmeqxcczqum9vdhkuernypkxzar9zsg8yatnw3ujumm6d3skyuewdaexwxszqy9pcpgptlhxvqq7yp9e58aguqr0rcun0ajlvmzq3ek63cw2w282gv3z5uupmuwvgjtq2sqxqqqquyqq8s" },
            { "offer": "e66d7beb93ef1b1084a73e5de6975ebc75c20d1a177bd2fb022b110226baf716",
              "bolt12": "lno1pqpq86q2xycnqvpsd4ekzapqv4mx2uneyqcnqgryv9uhxtpqveex7mfqxyk55ctw95erqv339ss8qun094exzarpzsg8yatnw3ujumm6d3skyuewdaexwxszqy9pcpgptlhxvqq7yp9e58aguqr0rcun0ajlvmzq3ek63cw2w282gv3z5uupmuwvgjtq2sqgqqxj7qqpp5hspuzq0pgmhkcg6tqeclvexaawhylurq90ezqrdcm7gapzvcyfzexkt8nmu628dxr375yjvax3x20cxyty8fg8wrr2dlq3nx45phn2kqru2cg",
              "bolt12_unsigned": "lno1pqpq86q2xycnqvpsd4ekzapqv4mx2uneyqcnqgryv9uhxtpqveex7mfqxyk55ctw95erqv339ss8qun094exzarpzsg8yatnw3ujumm6d3skyuewdaexwxszqy9pcpgptlhxvqq7yp9e58aguqr0rcun0ajlvmzq3ek63cw2w282gv3z5uupmuwvgjtq2sqgqqxj7qqpp5hsq" },
            { "offer": "7cef68df49fd9222bed0138ca5603da06464b2f523ea773bc4edcb6bd07966e7",
              "bolt12": "lno1qcp4256ypqpq86q2pucnq42ngssx2an9wfujqerp0y2pqun4wd68jtn00fkxzcnn9ehhyec6qgqsz83qfwdpl28qqmc78ymlvhmxcsywdk5wrjnj36jryg488qwlrnzyjczlqsp9nyu4phcg6dqhlhzgxagfu7zh3d9re0sqp9ts2yfugvnnm9gxkcnnnkdpa084a6t520h5zhkxsdnghvpukvd43lastpwuh73k29qsy",
              "bolt12_unsigned": "lno1qcp4256ypqpq86q2pucnq42ngssx2an9wfujqerp0y2pqun4wd68jtn00fkxzcnn9ehhyec6qgqsz83qfwdpl28qqmc78ymlvhmxcsywdk5wrjnj36jryg488qwlrnzyjczs" }]

    DATE_JAN1_2021 = 1609421400
    DAYS_SINCE = int((time.time() - DATE_JAN1_2021) // (60 * 60 * 24))
    return flask.render_template('examples.html'.format(network),
                                 API=flask.request.base_url, NETWORK=network,
                                     EXAMPLES=examples, DAYS_SINCE=DAYS_SINCE)


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
