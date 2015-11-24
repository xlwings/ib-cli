import ib.opt
import threading

from ib.ext.Contract import Contract

quit_event = threading.Event()
quit_event.clear()

def onMessage(msg):
    print msg
        

def onConnectionClosed(msg):
    quit_event.set()


import json
def ib_to_py(pl):
    if pl is None or isinstance(pl, (basestring, int, float, bool)):
        return pl
    elif isinstance(pl, (tuple, list)):
        return [ib_to_py(x) for x in pl]
    else:
        attrs = {}
        for attr in dir(pl):
            if attr.startswith("m_"):
                attrs[attr] = ib_to_py(getattr(pl, attr))
        return attrs

def details(args):
    ret = []

    def handler(msg):
        ret.append(ib_to_py(msg.contractDetails))

    def end_handler(msg):
        quit_event.set()
    
    args.connection.register(handler, ib.opt.message.contractDetails)
    args.connection.register(end_handler, ib.opt.message.contractDetailsEnd)
    args.connection.reqContractDetails(1, args.contract)

    return ret


# --------------------

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--secType', type=str, default='OPT')
parser.add_argument('--symbol', type=str, default='SPY')
parser.add_argument('--currency', type=str, default='USD')
parser.add_argument('--exchange', type=str, default='SMART')

parser.add_argument('--out', type=str, default='ib-cli-out.txt')

parser.add_argument('--quiet', action='store_true', default=False)
parser.add_argument('--pretty', action='store_true', default=False)

commands = parser.add_subparsers()

cmd = commands.add_parser('details')
cmd.set_defaults(func=details)

args = parser.parse_args()

args.connection = ib.opt.ibConnection('localhost', 4001, 1)
if not args.connection.connect():
    raise Exception("Could not connect")

if not args.quiet:
    args.connection.registerAll(onMessage)

args.connection.register(onConnectionClosed, ib.opt.message.connectionClosed)

args.contract = Contract()
args.contract.m_secType = args.secType
args.contract.m_symbol = args.symbol
args.contract.m_currency = args.currency
args.contract.m_exchange = args.exchange
#contract.m_right = "P"
#contract.m_expiry = '201511'
#contract.m_strike = 206.5
#contract.m_tradingClass = 'SPY'
#contract.m_multiplier = 100

res = args.func(args)

quit_event.wait()

with open(args.out, "w") as f:
    if args.pretty:
        json.dump(res, f, indent=2)
    else:
        json.dump(res, f)
