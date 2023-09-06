#!/usr/bin/env python3
import json
import os
import re
import time
import uuid
from pyln.client import Plugin, RpcError
from datetime import datetime, timedelta

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
def lnplaylive_createorder(plugin, node_count, hours):
    '''Returns a BOLT11 invoice for the given node count and time.'''
    try:
        # first let's ensure the values that they passed in are appropriate.
        rate_to_charge = None

        # ensure node_count is an int
        if not isinstance(node_count, int):
            raise Exception("Error: node_count MUST be a positive integer.")

        if node_count == 8:
            rate_to_charge = 200000
        elif node_count == 16:
            rate_to_charge = 220000
        elif node_count == 32:
            rate_to_charge = 240000
        elif node_count == 64:
            rate_to_charge = 260000
        else:
            raise InvalidCLNCountError("Invalid product. Valid node counts are 8, 16, 32, and 64.")

        # ensure hours is an int
        if not isinstance(hours, int):
            raise Exception("Error: hours MUST be a positive integer.")

        # ensure 'hours' is within acceptable limits
        if hours < 3:
            raise HoursTooLowException("The minimum hours you can set is 3.")
        elif hours > 504:
            raise HoursTooHighException("The maximum hours you can set is 504.")

        # calcuate the amount to charge in the invoice (msats) (msats per node hour)
        amount_to_charge = rate_to_charge * node_count * hours

        # we just need a guid to for cross referencing invoices. Order details for paid invoices are also stored in the
        # database under the label/guid bolt11_guid_str.
        bolt11_guid = uuid.uuid4()
        bolt11_guid_str = str(bolt11_guid)
        
        # generate the invoice
        description = f"lnplay.live - {node_count} nodes for {hours} hours."
        bolt11_invoice = plugin.rpc.invoice(amount_to_charge, bolt11_guid_str, description, 300)

        # create a BOLT12 offer.
        #bolt12_label = str(uuid.uuid4())
        #bolt12_invoice = "TODO"

        # get calculate an estimated expiration datetime for the vm environment.
        expiration_date = calculate_expiration_date(hours)

        # build an object to send back to the caller.
        createorder_response = {
            "node_count": node_count,
            "hours": hours,
            "expires_after": expiration_date,
            "bolt11_invoice_id": bolt11_guid_str,
            "bolt11_invoice": bolt11_invoice["bolt11"]
        }

        # everything in this object gets stored in the database and gets built upon by later scripts.
        createorder_dbdetails = {
            "node_count": node_count,
            "hours": hours
        }

        # let's store the order details in the datastore under the bolt11_guid_str
        # later execution logic can use this data in downstream calculations, and it's inconvenient 
        # to embed the order details in the actual invoice.
        plugin.rpc.datastore(key=bolt11_guid_str, string=json.dumps(createorder_dbdetails),mode="must-create")

        # now return the order details to the caller.
        json_data = json.dumps(createorder_response)
        json_dict = json.loads(json_data)
        return json_dict

    except RpcError as e:
        plugin.log(e)
        return e

# todo over time convert this to the wait rpc semantics.
@plugin.method("lnplaylive-invoicestatus")
def lnplaylive_invoicestatus(plugin, payment_type, invoice_id):
    '''Retuns the status of an invoice.'''

    try:
        valid_payment_types = ["bolt11", "bolt12"]

        if payment_type not in valid_payment_types:
            raise InvalidEnumerationError("Invalid payment type. Should be 'bolt11' or 'bolt12'.")

        # get info about the invoice and return it to the caller.
        invoices = plugin.rpc.listinvoices(invoice_id)

        matching_invoice = None
        for invoice in invoices["invoices"]:
            if invoice.get("label") == invoice_id:
              matching_invoice = invoice
              break

        if matching_invoice is None:
            raise InvoiceNotFoundError("BOLT11 invoice not found. Wrong invoice_id?")

        invoice_status = matching_invoice["status"]

        deployment_details = None
        matching_record = None

        if invoice_status == "paid":
            # the deployment details I need to pull from the datastore.
            # since the invoice is paid, we will need to consult the object in the data store.
            deployment_details = plugin.rpc.listdatastore(invoice_id)

            for record in deployment_details["datastore"]:
                if record.get("key")[0] == invoice_id:
                    matching_record = record
                    break

        deployment_details_json = "not_deployed"
        if matching_record is not None:
            deployment_details = matching_record["string"]
            deployment_details_json = json.loads(str(deployment_details))

        dbdetails_records = plugin.rpc.listdatastore(invoice_id)
        dbdetails = None
        for record in dbdetails_records["datastore"]:
            if record.get("key")[0] == invoice_id:
                dbdetails = record
                break

        node_count = None
        hours = None
        dbdetails_json = None
        if dbdetails is not None:
            dbdetails = dbdetails["string"]
            dbdetails_json = json.loads(str(dbdetails))

            if dbdetails_json is not None:
                node_count = dbdetails_json["node_count"]
                hours = dbdetails_json["hours"]

        invoicestatus_response = {
            "invoice_id": invoice_id,
            "node_count": node_count,
            "hours": hours,
            "payment_type": payment_type,
            "invoice_status": invoice_status,
            "deployment_details": deployment_details_json
        }

        json_data = json.dumps(invoicestatus_response)
        json_dict = json.loads(json_data)

        return json_dict

    except RpcError as e:
        plugin.log(e)
        return e

class InvalidEnumerationError(Exception):
    pass

class InvoiceNotFoundError(Exception):
    pass

class InvalidCLNCountError(Exception):
    pass

class HoursTooLowException(Exception):
    pass

class HoursTooHighException(Exception):
    pass

class WhatTheHellException(Exception):
    pass
    

@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):
    try:
        invoice_id = invoice_payment["label"]

        # let's get the invoice details.
        invoices = plugin.rpc.listinvoices(invoice_id)

        matching_invoice = None
        for invoice in invoices["invoices"]:
            if invoice.get("label") == invoice_id:
              matching_invoice = invoice
              break

        if matching_invoice is None:
            raise InvoiceNotFoundError("Invoice not found. Wrong invoice_id?")

        # let's grab the invoice description.
        invoice_description = matching_invoice["description"]
        if invoice_description.startswith("lnplay.live"):
            plugin.log(f"lnplay-live: invoice is associated with lnplay.live. Starting provisioning process. invoice_id: {invoice_id}")
        else:
            return

        # we pull the hours from the invoice description.
        number_of_hours = 0
        match = re.search(r'(\d+)\s+hours\.', invoice_description)
        if match:
            number_of_hours = int(match.group(1))

        if number_of_hours == 0:
            raise Exception("Could not extract number_of_hours from invoice description.")

        expiration_date = calculate_expiration_date(number_of_hours)

        # order_details resonse
        order_details = {
            "lnlive_plugin_version": lnlive_plugin_version,
            "vm_expiration_date": expiration_date,
            "status": "starting_deployment"
        }

        # add the order_details info to datastore with the invoice_label as the key
        plugin.rpc.datastore(key=invoice_id, string=json.dumps(order_details),mode="must-replace")

        # This is where we can start integregrating sovereign stack, calling sovereign stack scripts
        # to bring up a new VM on a remote LXD endpoint. Basically we bring it up,

        #connection_strings = ['connection_string0', 'connection_string1', 'connection_string2']
        # TODO add connection strings to object and update the record.


    except RpcError as e:
        printout("Payment error: {}".format(e))

def calculate_expiration_date(hours):

    # Get the current date and time
    current_datetime = datetime.now()
    time_delta = timedelta(hours=hours)
    expired_after_datetime = current_datetime + time_delta
    expiration_date_utc = expired_after_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
    return expiration_date_utc

plugin.run()  # Run our plugin
