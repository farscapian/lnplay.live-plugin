# lnplay.live-plugin

Core Lighting plugin for lnplay.live. Developed for the tabconf2023 hackathon.

## lnplaylive-createorder

`lnplaylive-createorder` is called by the front end web app to get an invoice for a product. Required parameters are node count (see product definition), number of hours the environment should be active (`hours`). The `description` field is any VALID JSON string that the front end wishes to include in the actual BOLT11 invoice. The front end and backend can agree on a format for this, but generally speaking, product customizations other details can be stored in this field. Note: the backend MAY embed additional details (e.g., version/git commits) in the `description` field. Invoice are created with a 300 second timeout (5 minutes).


### example

```bash
lightning-cli -k lnplaylive-createorder node_count=16 hours=48 description="test"
{
   "node_count": 16,
   "hours": 48,
   "bolt11_invoice_label": "9ebc0af9-fe5e-4b17-8683-fd689e486743",
   "bolt11": "lnbcrt800n1pj0tjlrsp5u...786gqalz9tg"
}
```

## lnplaylive-invoicestatus

The `lnplaylive-invoicestatus` rpc method returns the status of a BOLT11 invoice. The two required parameters are `payment_type`, which can be either 'bolt11' or 'bolt12', and `invoice_label`, which is [invoice label](https://docs.corelightning.org/reference/lightning-invoice) in the CLN database and is provided in the `lnplaylive-createorder` return value.

The front end can poll this rpc command to see if there are updates to invoice. The invoice status can change to `paid` or `expired`.

### example

```bash
lightning-cli -k lnplaylive-invoicestatus payment_type=bolt11 invoice_label="9ebc0af9-fe5e-4b17-8683-fd689e486743"
{
   "payment_type": "bolt11",
   "invoice_label": "9ebc0af9-fe5e-4b17-8683-fd689e486743",
   "invoice_status": "unpaid"
}
```
