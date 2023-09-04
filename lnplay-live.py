#!/usr/bin/env python3
import json
import os
import re
import uuid
from math import floor
from pyln.client import Plugin, RpcError
import uuid
from datetime import datetime

lnlive_plugin_version = "v0.0.1"

plugin_out = "/tmp/plugin_out"
if os.path.isfile(plugin_out):
    os.remove(plugin_out)

# use this for debugging-
def printout(s):
    with open(plugin_out, "a") as output:
        output.write(s)

plugin = Plugin()

@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):
    plugin.log("lnplay.live - plugin initialized")


@plugin.method("lnplaylive-createorder")
def lnplaylive_createorder(plugin, node_count, hours, description):
    '''Returns a BOLT11 invoice for the given node count and time.'''
    try:
        ## we just need a guid to for cross referencing invoices.
        bolt11_guid = uuid.uuid4()
        bolt11_guid_str = str(bolt11_guid)
        
        # rate is determined by product; in msats.
        rate_to_charge = 5000
        amount_to_charge = rate_to_charge * node_count
        bolt11_invoice = plugin.rpc.invoice(amount_to_charge, bolt11_guid_str, description, 300)

        bolt12_label = str(uuid.uuid4())
        bolt12_invoice = "TODO"
        bolt12_invoice = "TODO"

        createorder_response = {
            "node_count": node_count,
            "hours": hours,
            "bolt11_invoice_label": bolt11_guid_str,
            "bolt11": bolt11_invoice["bolt11"]
            #,
            #"bolt12_invoice_label": bolt12_label,
            #"bolt12_invoice": bolt12_invoice
        }

        json_data = json.dumps(createorder_response)
        json_dict = json.loads(json_data)
        return json_dict

    except RpcError as e:
        plugin.log(e)
        return e

# todo over time convert this to the wait rpc semantics.
@plugin.method("lnplaylive-invoicestatus")
def lnplaylive_invoicestatus(plugin, payment_type, invoice_label):
    '''Retuns the status of an invoice.'''

    try:
        valid_payment_types = ["bolt11", "bolt12"]

        if payment_type not in valid_payment_types:
            raise InvalidEnumerationError("Invalid payment type. Should be 'bolt11' or 'bolt12'.")

        # get info about the invoice and return it to the caller.
        invoices = plugin.rpc.listinvoices(invoice_label)

        matching_invoice = None
        for invoice in invoices["invoices"]:
            if invoice.get("label") == invoice_label:
              matching_invoice = invoice
              break

        invoicestatus_response = {
            "payment_type": payment_type,
            "invoice_label": invoice_label,
            "invoice_status": matching_invoice["status"]
        }

        json_data = json.dumps(invoicestatus_response)
        json_dict = json.loads(json_data)

        return json_dict

    except RpcError as e:
        plugin.log(e)
        return e

class InvalidEnumerationError(Exception):
    pass

@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):
    try:
        return "{}"
    except RpcError as e:
        printout("Payment error: {}".format(e))


plugin.run()  # Run our plugin
