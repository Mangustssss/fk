import json
from datetime import datetime
from currencies import cur
import smtplib
from random import choice
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import pypdf
from email import encoders
from email.mime.base import MIMEBase
import os
from playwright.sync_api import sync_playwright

SEJDA_API = "api_4BBAC598797143DBB33BE2975C462E70"

# def html_to_pdf(html_string, pdf_location, landscape=None):
#     if landscape:
#         landscape = "landscape"
#     url = 'https://api.sejda.com/v2/html-pdf'
#     r = requests.post(url, json = {
#         'htmlCode': html_string,
#         'pageSize':"a4",
#         "pageOrientation":landscape
#       }, headers = {
#         'Authorization': 'Token: {}'.format(SEJDA_API)
#       })
#     open("before_" + pdf_location, 'wb').write(r.content)
#
#     format_pdf(pdf_location, pdf_location, landscape)

def html_to_pdf_2(html_content, output_path, landscape=False):
    with sync_playwright() as p:
        # executable_path = "C:\\Users\\nikit\\Downloads\\chrome-win\\chrome.exe"
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        # Set the content of the page to your HTML
        page.set_content(html_content)

        # Wait for a moment to ensure the content is loaded
        page.wait_for_timeout(2000)

        # Generate PDF from the page content
        page.pdf(path=output_path, format='A4', landscape=landscape, margin=dict(top="0", right="0", bottom="0", left="0"))

        browser.close()

# def format_pdf(pdf_in, pdf_out, landscape=None):
#     pdf_path = fr'{pdf_in}'
#     output_path = fr'{pdf_out}'
#     pdf = pypdf.PdfReader(pdf_path)
#     writer = pypdf.PdfWriter()
#     page0 = pdf.pages[0]
#     # page0.scale_by(1.3)
#     # if landscape:
#     #     page0.mediabox.lower_right = (841.890, page0.mediabox.top - 595.276)#landscape
#     # else:
#     #     page0.mediabox.lower_right = (595.276, page0.mediabox.top - 841.890)#portrait
#     writer.add_page(page0)
#     with open(output_path, "wb+") as f:
#         writer.write(f)

class CustommedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def get_keys(receipt):
    file_name = f"receipts/template_{receipt.replace(' ', '_')}.html"
    with open(file_name, "r", encoding='utf-8') as f:
        if "paper" in receipt:
            keys = [a[0] for a in [i.split("%}") for i in f.read().split('{%')][1:]]
        else:
            keys = [a[0] for a in [i.split("}") for i in f.read().split('{')][1:]]
    return set(keys)

def save_html_template(short_receipt_name, html_code):
    with open("receipts/template_" + short_receipt_name.replace(" ", "_") + ".html", "w", encoding='utf-8') as f:
        f.write(html_code)

def delete_html_template(short_receipt_name):
    os.remove("receipts/template_" + short_receipt_name.replace(" ", "_") + ".html")

def format_randoms(random_formats):
    if random_formats == "":
        return []
    randoms = {}
    formats = random_formats.split(";")
    for i in formats:
        key, value = i.split(":")
        randoms[key] = value
    return randoms

def format_dates(date_formats):
    if date_formats == "":
        return []
    dates = {}
    formats = date_formats.split(";")
    for i in formats:
        key, value = i.split(":")
        dates[key] = value
    return dates

def save_info(short_receipt_name, email, password, date_format, subject, random_formats, required_keys):

    with open("info.json", "r", encoding='utf-8') as f:
        creds = json.load(f)

    randoms = format_randoms(random_formats)
    dates = format_dates(date_format)

    for i in randoms:
        if i not in required_keys and i != "position":
            raise CustommedException(f"There is no {i} key(randoms)")

    for i in dates:
        if i not in required_keys:
            raise CustommedException(f"There is no {i} key(dates)")

    creds[short_receipt_name] = {"email":email,
                                 "password":password,
                                 "subject": subject,
                                 "date_format": dates,
                                 "random_formats": randoms}

    with open("info.json", "w", encoding='utf-8') as f:
        json.dump(creds, f)

def new_receipt(html_code, date_format, random_formats, subject, receipt_name, email, password):

    short_receipt_name = receipt_name.replace(" email", "")

    save_html_template(short_receipt_name, html_code)

    required_keys = get_keys(short_receipt_name)

    if "date" in required_keys and date_format == "":
        raise CustommedException("Date format is not written")

    if subject == "":
        raise CustommedException("Subject is not written")

    save_info(short_receipt_name, email, password, date_format, subject, random_formats, required_keys)

# file_names = [f for f in os.listdir("../receipts")]
# for i in file_names:
#     print(i)
#     with open(f"../receipts/{i}", "r", encoding="utf-8") as f:
#         html_code = f.read()
#     while True:
#         date_format = input("-----------\nDate_format:")
#         random_form = input("-----------\nRandom_formats:")
#         subject = input("-----------\nSubject:")
#         email = input("-----------\nEmail:")
#         passw = input("-----------\nPassword:")
#         right_info = input("---------------\n-------------\nALL GOOD(y,n,s):")
#         if right_info == "y":
#             new_receipt(html_code=html_code,
#                         date_format=date_format,
#                         random_formats=random_form,
#                         subject=subject,
#                         receipt_name=i.replace("template_", "").replace(".html", "").replace("_", " ") + ' email',
#                         email = email,
#                         password = passw)
#             break
#         elif right_info == "n":
#             pass
#         elif right_info == "s":
#             break
#         else:
#             break
def choose_cur(curen: str):
    return cur[curen.upper()]['symbol']

def delete_cur(order):
    del_cur = ['price', 'ship', 'total']
    for i in del_cur:
        try:
            order[i] = order[i].replace(choose_cur(order['cur']), "")
        except KeyError:
            pass
    return order

def get_date(order):
    short_receipt_name = order['ordername'].replace(" email", "")
    with open("info.json", "r", encoding='utf-8') as f:
        all_info = json.load(f)
    if all_info[short_receipt_name]["date_format"] == {}:
        return order
    else:
        for i in all_info[short_receipt_name]['date_format']:
            order[i] = datetime.strptime(order['date'], "%Y-%m-%d").strftime(all_info[short_receipt_name]['date_format'][i])
    return order

def random_bukv(n):
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
               'v', 'w', 'x', 'y', 'z']
    return "".join([choice(letters) for i in range(n)])

def random_code_dig(num):
    digits = list('1234567890')
    return "".join([choice(digits) for i in range(num)])


def get_randoms(order):
    short_receipt_name = order['ordername'].replace(" email", "")
    with open("info.json", "r", encoding='utf-8') as f:
        all_info = json.load(f)
    randoms = all_info[short_receipt_name]['random_formats']
    for i in randoms:
        random = randoms[i].split('/')
        for parts in range(len(random)):
            if random[parts].startswith("%d"):
                random[parts] = random_code_dig(int(random[parts].replace("%d", "")))
            elif random[parts].startswith("%b"):
                random[parts] = random_bukv(int(random[parts].replace("%b", ""))).upper()
        order[i] = "".join(random)
    return order

def get_subject(receipt_name):
    with open("info.json", "r", encoding='utf-8') as f:
        all_info = json.load(f)
    return all_info[receipt_name.replace(" email", "")]['subject']

def get_template(receipt_name: str):
    with open(f"receipts/template_{receipt_name.replace(' email', '').replace(' ', '_')}.html", "r", encoding='utf-8') as f:
        temp = f.read()
    return temp

def print_out_diff(keys_from_order, keys_from_receipt):

    add = [item for item in keys_from_order if item not in keys_from_receipt]
    must_be = [item for item in keys_from_receipt if item not in keys_from_order]

    if must_be != []:
        raise CustommedException(f"not all required data - {must_be}")


def get_message(order, login):

    order = get_date(order)
    order['cur_name'] = str(order['cur'])
    order['cur'] = choose_cur(order['cur'])
    order = get_randoms(order)
    msg = MIMEMultipart()
    msg['To'] = order['email']
    msg['From'] = login
    subject = get_subject(order['ordername'])

    temp = get_template(order['ordername'])
    print_out_diff(order.keys(), get_keys(order['ordername'].replace(' email', '')))

    for i in order:
        temp = temp.replace("{" + f"{i}" + "}", str(order[i]))
        subject = subject.replace("{" + f"{i}" + "}", str(order[i]))
    msg['Subject'] = subject
    msg.attach(MIMEText(temp, 'html'))
    return msg

def get_message_paper(order, login):

    order = get_date(order)
    order['cur_name'] = str(order['cur'])
    order['cur'] = choose_cur(order['cur'])
    order = get_randoms(order)
    msg = MIMEMultipart()
    msg['To'] = order['email']
    msg['From'] = login
    subject = get_subject(order['ordername'])

    temp = get_template(order['ordername'])
    print_out_diff(order.keys(), get_keys(order['ordername'].replace(' email', '')))

    for i in order:
        temp = temp.replace("{%" + f"{i}" + "%}", str(order[i]))
        subject = subject.replace("{%" + f"{i}" + "%}", str(order[i]))
    msg['Subject'] = subject
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(temp)
    if order['position'] == "landscape":
        html_to_pdf_2(temp, "paper.pdf", landscape=True)
    else:
        html_to_pdf_2(temp, "paper.pdf")

    attachment = open("paper.pdf", 'rb')  # r for read and b for binary
    attachment_package = MIMEBase('application', 'octet-stream')
    attachment_package.set_payload((attachment).read())
    encoders.encode_base64(attachment_package)
    attachment_package.add_header('Content-Disposition', "attachment; filename= " + "paper.pdf")
    msg.attach(attachment_package)
    return msg

def get_creds(receipt_name):
    with open("info.json", "r", encoding='utf-8') as f:
        if "email" in  receipt_name:
            creds = json.load(f)[receipt_name.replace(" email", "")]
        elif "paper" in receipt_name:
            creds = json.load(f)[receipt_name]
        else:
            raise Exception("Receipt is not automated")
        return creds['email'], creds['password']

def send_receipt(order):
    try:
        order['ordername'] = order['ordername'].replace(' INVOICE', '').lower()
        order = delete_cur(order)
        if 'acf_name' in order:
            order['name'] = order['acf_name']
        if 'acf_surname' in order:
            order['surname'] = order['acf_surname']

        if order['ordername'].endswith('app'):
            return False, "App cant be made"

        login, passsword = get_creds(order['ordername'])

        if 'paper' in order['ordername']:
            message = get_message_paper(order, login)
        else:
            message = get_message(order, login)
        recipient_email = order['email']

        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.starttls()
        smtp_server.login(login, passsword)

        smtp_server.sendmail(login, recipient_email, message.as_string())
        smtp_server.quit()


    except Exception as e:
        print(f"EXCEPTION!: {e}")
        return False, e
    return True, 200

def delete_automated_receipt(ordername):
    ordername = ordername.replace(' INVOICE', '').lower()
    short_name = ordername.replace(" email", "")
    with open("info.json", "r", encoding="utf-8") as f:
        info = json.load(f)
    del info[short_name]
    with open("info.json", "w", encoding="utf-8") as f:
        json.dump(info, f)
    delete_html_template(short_name)

def get_all_automated_receipts():
    with open("info.json", "r", encoding='utf-8') as f:
        info = dict(json.load(f))
    return list(info.keys())

# send_receipt({"us_size":"11", "price":'100', "ship":'12', "cur":"USD", 'date':"2023-12-19", "name_prod":"BEST PRODUCT NAME", "tax":"12", "img_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Image_created_with_a_mobile_phone.png/330px-Image_created_with_a_mobile_phone.png", "style": "FKstyle", "total":"3000", "email":'nikita.rjabokons.12@rpg.lv', "ordername": "STOCKX EMAIL INVOICE"})
