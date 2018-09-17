from __future__ import print_function
import re
from email.mime.text import MIMEText
import base64
from oauth2client import file, client, tools
from googleapiclient.discovery import build
from httplib2 import Http
import argparse

wordDict = dict()

def insertWord(matchobj):
    if matchobj:
        pattern = matchobj[0]
        if pattern not in wordDict:
            wordDict[pattern] = input(matchobj[0] + ": ")
        return wordDict[pattern]

def getGmailApiService():
    SCOPES = "https://www.googleapis.com/auth/gmail.send"
    store = file.Storage('email_generator_credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    return build('gmail', 'v1', http=creds.authorize(Http()))

def create_message(sender, to, subject, message_text, cc):
    """Create a message for an email.

    Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

    Returns:
    An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    if cc:
        message['cc'] = cc
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
    """
    try:
        message = (service.users().messages().send(userId='me', body=message).execute())
        print("Message Id: %s" % message['id'])
        return message
    except Exception as error:
        print("An error occurred: %s" % error)    

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Enter the name of the template file")
parser.add_argument("--to", help="Enter the email address of the person who you would like to send the email to. If you don't add it here you will be prompted to enter it.")
parser.add_argument("--subject", help="Enter the subject of the email. If you don't add it here you will be prompted to enter it.")
parser.add_argument("--cc", help="Enter who you would like to be cc'd on this email.")
args = parser.parse_args()    
toEmail = args.to
if not toEmail:
    toEmail = input("What is the email address of the person you would like to send this to?: ")
emailSubject = args.subject
if not emailSubject:
    emailSubject = input("What is the subject of this email?: ")
print("Enter the replacement words for the following:")
templateFile = open(args.filename, "r")
template = templateFile.read()
templateFile.close()
template = re.sub('\{(.*?)\}', insertWord, template)
print("Send to: %s" % toEmail)
print("Subject: %s" % emailSubject)
print("cc: %s" % args.cc)
print(template)
if input("Would you like to send the message? (Y/N)").upper() == "Y":
    message = create_message("me", toEmail, emailSubject, template, args.cc)
    serv = getGmailApiService()
    send_message(serv, "me", message)
