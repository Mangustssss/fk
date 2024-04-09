from sellix import Sellix
import time

client = Sellix("6pdLxUB8cSdkFZXtxxXwxFg7mHMDHJ4To6lY3Cmbu53VrkEv74101slMLuRZup3X", 'fkpayment')

print(client.get_order("8cc54a-4cff60c294-f91f2b"))

# invoice_to_check = """34912d-e3c4f4a55c-ca098b
# 3c18ad-6506825dd3-c9f396
# 887862-bd501ad2a6-a57bc8
# 76003f-61f8ed078f-642cd1
# 6d5ff9-ba5be8d0dc-2e2b3c
# abe651-272e7520ed-88cfe2
# 7ebad9-a5ed466a77-5da9bd
# ee53eb-450b7cdce2-1273a2
# 3200d3-0a3a8a82c6-065b3c
# 6e1166-1d80c6b6ce-12c978
# 1b12bf-0f9d66261c-e6325d
# 05829c-60983250db-98aedb
# cf1390-cfff7398c6-724a85
# 8335ae-073ad8648d-cabdf1
# b4f046-706a0491aa-6be148
# caa60d-a5f650245d-2c9584
# 0fa89d-8f35742850-c68e02
# 52ff56-d115a5f397-75b0f2
# c2ddcd-1627105940-a3e43c
# 094177-0c35d7eb7c-4b4ded
# 5e3c40-2c9f9c153d-4092f8
# 0bdc8f-8754d2020d-5972ab
# b87931-d21468e7d6-9643e6
# 569713-f8f359646b-73e5f8
# 0187e9-c905fc8b19-32efff
# b5cfcf-47f8e9b4a4-af95ac
# 5466bc-5bbfe1a31c-1bc2f8
# f074dc-e6c0ea2368-821a63
# 0df73c-d18a95d823-ca950c
# d31fdb-040db8db0b-dc16c9
# d568a7-7d15a5639e-53783f
# fbb2fc-44e3f82930-efcf0f
# de6e65-f508e013f1-1df25a
# a416a4-8b47b72222-7ae4b5
# 82216e-d91f8652d6-35cd3e
# 69c3f5-e853f2fb0d-ccec9b
# 76d70b-73c5d2a4d8-248f11
# 0668de-2e12a30962-d03df3
# 9e22c6-97b472201e-574195
# 06a445-9a7e82f3fc-bc7674
# 5ac489-743b1814e6-8ee71a
# a84c96-db5a9aec9a-1cc237
# c59e31-908bfbbeba-9cce92
# """.split("\n")
#
# orders = {}
#
# for i in invoice_to_check:
#     invoice = client.get_order(i)
#     time.sleep(2)
#     print(invoice['status'])
#     # try:
#     #     if
#     #         if invoice['custom_fields']['order_date']['instagram'] in orders:
#     #             orders[invoice['custom_fields']['order_date']['instagram']] += 1
#     #         else:
#     #             orders[invoice['custom_fields']['order_date']['instagram']] = 1
#     # except TypeError:
#     #     pass
#
# # for i in orders:
# #     if orders[i] == 0
# #     print(i)