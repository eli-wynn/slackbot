import subprocess
import constants
import smtplib, ssl
import pytz
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from shotgun_api3 import Shotgun, ShotgunError

SERVER_PATH = 
SCRIPT_NAME = 
SCRIPT_KEY = 

sg = Shotgun(SERVER_PATH, SCRIPT_NAME, SCRIPT_KEY)

def current_time():
    return str(datetime.today().strftime('%I:%M %p'))

def current_time_stock():
    stock_tz = pytz.timezone('Europe/Stockholm')
    stock_time = datetime.now(stock_tz)
    return stock_time.strftime('%I:%M %p')

def current_time_la():
    la_tz = pytz.timezone('America/Los_Angeles')
    la_time = datetime.now(la_tz)
    return la_time.strftime('%I:%M %p')

def current_time_aus():
    syd_tz = pytz.timezone('Australia/Sydney')
    syd_time = datetime.now(syd_tz)
    return syd_time.strftime('%I:%M %p')


def to_day():
    return str(datetime.today().strftime('%Y-%m-%d'))

def dayAdder(daysAdded):
    today = datetime.now()
    tomorrow = today + timedelta(days=daysAdded)
    return str(tomorrow.strftime('%Y-%m-%d'))

def humanReadable(date):
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    human_readable_date = date_obj.strftime("%B %d %Y")
    return human_readable_date

def getMixtape():
    username = "example@gmail.com"
    password = constants.email_pass  # Use the application-specific password here

    # Create an SSL context to secure the connection
    context = ssl.create_default_context()

    # Connect to the Gmail IMAP server
    with imaplib.IMAP4_SSL("imap.gmail.com", port=993, ssl_context=context) as mail:
        # Login to the email account
        mail.login(username, password)
        # Select the mailbox you want to use (in this case, the inbox)
        mail.select("inbox")

        # Search for emails with the subject "Mixtape Monday"
        status, messages = mail.search(None, '(SUBJECT "Mixtape")')
        
        if status != "OK":
            print("No messages found.")
            return

        # Convert messages to a list of email IDs
        email_ids = messages[0].split()
        
        if not email_ids:
            print("No messages found.")
            return
        
        # Fetch the most recent email (last one in the list)
        latest_email_id = email_ids[-1]

        # Fetch the email by ID
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        
        if status != "OK":
            print("Failed to fetch email.")
            return

        # Parse the email content
        msg = email.message_from_bytes(msg_data[0][1])
        sender = msg["from"]
        
        # Decode the email subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            # If it's a bytes type, decode to str
            subject = subject.decode(encoding if encoding else "utf-8")
        
        # Get the email date
        date = msg["Date"]
        
        # Get the email snippet (the plain text or the first part of the email)
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    snippet = part.get_payload(decode=True).decode()
                    tuple = (snippet, sender)
                    return tuple
                    break
        else:
            snippet = msg.get_payload(decode=True).decode()
        
        return "Mixtapes could not be located"


def sendEmail(text, receiver, subject):
    sender_email = "example@gmail.com"
    password = constants.email_pass  # Use the application-specific password here

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Create the email content
    msg = MIMEText(text)
    msg['From'] = sender_email
    msg['To'] = receiver
    msg['Subject'] = subject

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls(context=context)  # Secure the connection
        server.login(sender_email, password)  # Log in to the server
        server.sendmail(sender_email, receiver, msg.as_string())  # Send the email

#project
def project(argument, sg):
    filters = [
        ['sg_status_list', 'is', 'act'], #filters only active projects
        ['projects', 'name_contains', argument] #filters names containing the input argument
    ]

    #finds the name, email, job titles and projects of human users who fit the filter
    projs = sg.find( 
        "HumanUser",  
        filters=filters, 
        filter_operator="and",
        fields=['name', 'email', 'sg_job_title', 'projects']  
    )
    
    storage = [] 

    
    for user in projs: #takes only the name, email and job title of human users who were left after filter
        item = []
        item.append(user['name'])
        item.append(user['email'])
        item.append(user['sg_job_title'])
        storage.append(item)
    return storage 


#need to fix capitalization issue here (how to deal with stuff like vfxSupervisor and Camera-Layout in the same vein without hard coding)
def role(argument, sg):
    filters = [
        ['sg_status_list', 'is', 'act'],
    ]
    #query shotgrid for human users and pull the name, email, job title and department based on the filters above
    roles = sg.find(
        "HumanUser",  
        filters=filters,
        filter_operator="and",
        fields=['name', 'email', 'sg_job_title', 'department']  
    )
    
    storage = []  

    for user in roles:
        item = []
        item.append(user['name'])
        item.append(user['email'])
        item.append(user['sg_job_title'])       #try and pull all the ones that match the queried department
        try:                                    #try except prevents failure due to an active user not having a department (some users are not labelled)
            x = user['department']
            name = x['name']
            name = name.lower()
            if(name == argument):
                item.append(name)
                storage.append(item)
        except Exception as e:
            continue
    return storage


def getTasksDue(content, date): 
    #put content back in input field
    duo = ['ip', 'rdy']

    lebron = find_active_projects(sg)
    
    filters = [
        ['sg_status_list', 'in', duo],
        ['project', 'in', lebron],
        ['due_date', 'is', date]
    ]

    project = sg.find(
        "Task",
        filters=filters, 
        filter_operator="and",
        fields= ['entity','project','task_assignees', 'sg_description', 'step', 'due_date']
    )
    storage = []

    for task in project:
        item = []
        x = task['entity']
        item.append(x['name'])
        x = task['project']
        item.append(x['name'])
        x = task['task_assignees']
        
        # Since task_assignees is a list, iterate through it and get names
        assignee_names = ', '.join([assignee['name'] for assignee in x])
        item.append(assignee_names)
        
        item.append(task['sg_description'])
        x = task['step']
        item.append(x['name'])
        item.append(task['due_date'])
        storage.append(item)

    return storage #need to pull relevant info from each line of project to send over (it is exceeding the length rn)

#returns a list of all active projects in shotgrid
def find_active_projects(sg):
    return sg.find(
        'Project',
        [['sg_status', 'is', 'Active'], ['sg_production_status', 'is', 'curnt'],['sg_type', 'is_not', 'Misc.'], ['updated_at', 'in_last', 1, 'MONTH']],
        [
            'id'
        ]
    )



