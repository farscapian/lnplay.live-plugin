# lnplay.live-plugin

Core Lighting plugin for lnplay.live. Developed for the tabconf2023 hackathon.

## lnplaylive-createorder

`lnplaylive-createorder` is called by the front end web app to get an invoice for a product. Required parameters are node count (see product definition), number of hours the environment should be active (`hours`) (minimum 3). The `description` field is any VALID JSON string that the front end wishes to include in the actual BOLT11 invoice. The front end and backend can agree on a format for this, but generally speaking, product customizations other details can be stored in this field. Note: the backend MAY embed additional details (e.g., version/git commits) in the `description` field. Invoice are created with a 300 second timeout (5 minutes).

### example

```bash
lightning-cli-k lnplaylive-createorder node_count=16 hours=3 description=" {\"field0\": true, \"field1\": testing}"
{
   "node_count": 16,
   "hours": 3,
   "bolt11_invoice_id": "aec62c5a-3dcb-41d6-ab85-3b8da6b5356f",
   "bolt11_invoice": "lnbcrt3520n1pj0tkwksp5...9h53z",
   "bolt12_invoice_id": "fc1946bb-1ca2-41f8-b352-ddf7d919c601",
   "bolt12_invoice": "TODO"
}
```

## lnplaylive-invoicestatus

The `lnplaylive-invoicestatus` rpc method returns the status of a BOLT11 invoice. The two required parameters are `payment_type`, which can be either 'bolt11' or 'bolt12', and `invoice_id`, which is [invoice label](https://docs.corelightning.org/reference/lightning-invoice) in the CLN database and is provided in the `lnplaylive-createorder` return value.

The front end can poll this rpc command to see if there are updates to invoice. The invoice status can change to `paid` or `expired`.

### example

```bash
lightning-cli -k lnplaylive-invoicestatus payment_type=bolt11 invoice_id="aec62c5a-3dcb-41d6-ab85-3b8da6b5356f"
{
   "payment_type": "bolt11",
   "invoice_id": "aec62c5a-3dcb-41d6-ab85-3b8da6b5356f",
   "invoice_status": "unpaid"
}
```
