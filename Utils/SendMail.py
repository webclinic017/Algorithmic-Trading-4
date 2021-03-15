import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from Services.SimViewer import StrategyView
from Services.TradingClock import TradingClock

from _devconfig import *



def generate_message(simtracker, account):
    clock = TradingClock.getInstance()

    # TODO: Make one big email
    # https://stackoverflow.com/questions/920910/sending-multipart-html-emails-which-contain-embedded-images

    # The mail addresses and password
    sender_address = MY_EMAIL
    sender_pass = MY_EMAIL_PASS

    # Setup the MIME
    message = MIMEMultipart('related')
    message_alt = MIMEMultipart('alternative')
    message.attach(message_alt)

    message_brief = MIMEMultipart('related')
    message_alt_brief = MIMEMultipart('alternative')
    message_brief.attach(message_alt_brief)

    message_text = ""
    message_text_brief = ""
    while len(simtracker.snapshots):
        snapshot = simtracker.snapshots.pop(0)

        symbol = snapshot.contract.symbol
        action = snapshot.order.action
        file = f"C:/Users/liamd/Documents/Project/AlgoTrading/Output/Emails/{symbol}_{action}_{clock.sync_datetime.strftime('%m%d%h')}.png"
        fig, ax, leg_indicators = StrategyView.snapshot_to_fig(snapshot, account, savefile=file)


        # We reference the image in the IMG SRC attribute by the ID we give it below
        message_text += f'<p>{snapshot.name} - SYMBOL: {symbol},  ACTION: {action},  DATE:{snapshot.data.index[-1]} </p>' + \
                        f'<br><img src="cid:image_{symbol}">' + \
                        f'<br>' + \
                        f'<p>' + ', '.join([k + ': ' + v for k, v in leg_indicators.items()]) + '</p>' + \
                        f'<br>'

        message_text_brief += f'<p>{snapshot.name} - SYMBOL: {symbol},  ACTION: {action},  DATE:{snapshot.data.index[-1]} </p>' + \
                              f'<br>'


        # This example assumes the image is in the current directoryddd
        fp = open(file, 'rb')
        msg_image = MIMEImage(fp.read())
        fp.close()


        # Define the image's ID as referenced above
        msg_image.add_header('Content-ID', f'<image_{symbol}>')
        message.attach(msg_image)

    msg_text = MIMEText(message_text, 'html')
    message_alt.attach(msg_text)

    msg_text_brief = MIMEText(message_text_brief, 'html')
    message_alt_brief.attach((msg_text_brief))


    message['From'] = sender_address
    message['Subject'] = 'Paper Trades'
    message.preamble = 'This is a multi-part message in MIME format.'

    message_brief['From'] = sender_address
    message_brief['Subject'] = 'Paper Trades'
    message_brief.preamble = 'This is a multi-part message in MIME format.'

    # Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    session.login(sender_address, sender_pass)

    message['To'] = sender_address
    session.sendmail(sender_address, sender_address, message.as_string())

    for receiver_address in EMAIL_LIST:
        message_brief['To'] = receiver_address
        session.sendmail(sender_address, receiver_address, message_brief.as_string())


    session.quit()






