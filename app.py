# Name: Dreambot - Projects
# Description: Slack bot interface to allow users to call commands and access sensitive information from outside the network
# Language: Python3
# API's Used: ShotGrid API V3, Jira/Atlassian RestAPI V3, Slack API
# Creators: Eli Wynn, Owen Reid
# Date Created: 07/18/2024 (July 18, 2024)
# Copyright: Mavericks-VFX 2024
import os
import backend
import constants
import subprocess
import requests
import re
import Deadline.DeadlineConnect as Connect
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

#establishes connection with slack
app = App(
    token= constants.token,
    signing_secret= constants.signing_secret, 
)
deadcon =  Connect.DeadlineCon()


"""
Creates a breach alert on OpsGenie (for use in emergencies only).
"""
@app.command("/breach")
def breach(ack, body, logger, client, command):
    ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    argument = command["text"]
    response = client.users_info(user=user_id)
    
    # Extract user email from response
    user_email = response["user"]["profile"]["email"]
    email_content = f"Breach alert submitted by: {user_email}\n\n{argument}"
    
    # Block accidental submissions since any real breach would be >4 characters
    if len(argument) > 4:
        try:
            backend.sendEmail(
                email_content,
                "example@gmail.com",
                "Potential User Reported Breach - Submitted Through DreamBot"
            )
            output = "/breach \nBreach email successfully sent to: example@gmail.com"
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": output},
                    }
                ],
                text=output
            )
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"An error occurred: {e}"
            )

"""
Creates a 911 alert on OpsGenie (Only for actual 911 events, e.g., fire in the office).
"""
@app.command("/911")
def sos(ack, body, logger, client, command):
    ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    argument = command["text"]
    response = client.users_info(user=user_id)
    
    # Extract user email from response
    user_email = response["user"]["profile"]["email"]
    email_content = f"911 Message from user: {user_email}\n\n{argument}"
    
    # Block accidental submissions since any real 911 event would be >4 characters
    if len(argument) > 4:
        try:
            backend.sendEmail(
                email_content,
                "example@gmail.com",
                "DreamBot 911"
            )
            output = "/911: \n911 email successfully sent to: example@gmail.com"
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": output},
                    }
                ],
                text=output
            )
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"An error occurred: {e}"
            )


"""
Displays a list of all relevant links
"""
@app.command("/links")
def links(ack, body, logger,say):
    ack()
    logger.info(body)
    output = "/links company links (removed actual links for security concerns)"
    say(
        blocks =[
            {
               "type": "section",
                "text": {"type": "mrkdwn", "text": output}
            },
        ],
        text = output
    )


"""
RolLcall (showcode, department) - All users associated with group in ShotGrid.
Department or shotcode must match exactly (case insensitive).
E.g., Camera-Layout or camera-layout works, but cameralayout doesn't.
"""
@app.command("/rollcall")
def rollcall(ack, body, logger, client, command, say):
    ack()
    logger.info(body)
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    argument = command["text"]
    
    # Remove whitespace
    argument = argument.replace(" ", "")
    output = ""
    try:
        
        # Check if input argument matches a department
        role = backend.role(argument.lower(), backend.sg)
        
        # If role returns anything other than an empty string, it was a department
        if len(role) > 0:
            output += "Department: " + argument.title()
            output += '\n\n'
            output += formatRoles(role)
        
        
        else:
            output = "Please enter a valid show code or department"
        
        # client.chat_postEphemeral(
        #     channel=channel_id,
        #     user=user_id,
        say(
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```" + output + "```"},
                }
            ],
            text=output
        )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"An error occurred: {e}"
        )

"""
Slack /command that sends the data from today's deliveries to Slack 
and displays it in response to /today.
"""
@app.command("/today")
def due(ack, body, logger, client, say):
    ack()
    logger.info(body)
    txt = "/today\n" + get_today_deliveries()

    # Uncomment and remove the "say(" to return it to ephemeral (only caller of command can see)
    # user_id = body['user_id']
    # channel_id = body['channel_id']
    
    # client.chat_postEphemeral(
    #     channel=channel_id,            
    #     user=user_id,
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": txt}
            }
        ],
        text=txt
    )

"""
Slack /command that sends the data from this week's deliveries to Slack 
and displays it in response to /due.
"""
@app.command("/due")
def due(ack, body, logger, say):
    ack()
    logger.info(body)

    txt = "/due\n" + get_deliveries_text()
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": txt}
            }
        ],
        text=txt
    )

"""
Returns the most recent Mixtape Monday (note the Spotify link only 
expands once per channel).
"""
@app.command("/mixtape")
def mixtape(ack, body, logger, say):
    ack()
    logger.info(body)
    
    # Returns a tuple with the sender data and Spotify link
    mixy = backend.getMixtape()
    
    # Get sender data from getMixtape()
    sender = mixy[1]
    
    # Regex search for the Spotify link
    link = re.search(r"https:\/\/open\.spotify\.com\/[A-Za-z0-9\/?=&]+", mixy[0])
    mixy = "/mixtape\nMixtape Monday from " + sender + "\n" + link.group()
    
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": mixy},
            }
        ],
        text=mixy
    )

"""
Calls the data from the get_houdini_licenses and displays it in Slack.
"""
@app.command("/whohou")
def whohou(ack, body, logger, say):
    ack()
    logger.info(body)
    
    license_text = "/whohou\n" + get_whohou_text()
    
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": license_text},
            }
        ],
        text=license_text
    )


"""
Calls the data from the get_nuke_licenses and displays it in Slack.
"""
@app.command("/whonuke")
def whonuke(ack, say):
    ack()

    output = "/whonuke\n" + get_nuke_text()

    say(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": output,
                },
            }
        ],
        text=output
    )

"""
/whoasset followed by a username returns all assets checked out by 
said user by calling the whoasset command.
"""
@app.command("/whoasset")
def whoasset(ack, say, command, body):
    ack()
    argument = command["text"]

    try:
        # Run the whoasset commandline command
        user_command = f'whoasset {argument}'
        result = subprocess.run(['bash', '-c', user_command], capture_output=True, text=True)
        output = "/whoasset " + argument + "\n" + result.stdout.strip()

        say(
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": output},
                }
            ],
            text=output
        )
    except:
        say("Please enter a valid user")

"""
/renderstatus followed by a show code or username returns the current jobs 
associated with said show/user.
"""
@app.command("/renderstatus")
def renderstatus(ack, logger, command, client, say):
    ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    argument = command["text"]

    try:
        # Returns all renders associated with a username
        output = user(argument)
        
        # Splits to check if there are render jobs
        tester = output.split()
        
        # User returns "Showing" as the first word if there is a render job associated
        # with the input user
        if tester[6] == 'No':
            output = "/renderstatus " + argument + "\n" + job_by_name(argument)

        
        say(
        # client.chat_postEphemeral(
        #     channel=channel_id,
        #     user=user_id,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```" + output + "```"},
                }
            ],
            text=output
        )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"An error occurred: {e}"
        )

@app.command("/renders")
def renders(ack, logger, command, say, client):
    ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    argument = command["text"]

    try:
        output = all_jobs()
          
        say(
        # client.chat_postEphemeral(
        #     channel=channel_id,
        #     user=user_id,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```" + output + "```"},
                }
            ],
            text=output
        )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"An error occurred: {e}"
        )

"""
Displays the user's render progress.
"""
@app.command("/myrender")
def myrender(ack, logger, command, client):
    ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]

    try:
        # Call the Slack API to get user info including email
        response = client.users_info(user=user_id)
        
        # Extract user email from response
        user_email = response["user"]["profile"]["email"]
        holder = user_email.split("@")
        username = holder[0]
        
        # Calls and formats user (user gets all renders associated with a name)
        output = f"```" + "/myrender\n" + user(username) + "```"
    
        # Post an ephemeral message back to the user
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": output},
                }
            ],
            text=output
        )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"An error occurred: {e}"
        )

"""
/studiotime followed by a studio or location returns the time at 
said studio or location. If the argument is nothing, it returns all studio times.
"""
@app.command("/studiotime")
def studiotime(ack, logger, command, client, say):
    ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    argument = command["text"]
    
    # Fetch EST current time
    est = backend.current_time()
    
    # Fetch current time in Stockholm
    cest = backend.current_time_stock()

    # Fetch current time in Los Angeles
    pdt = backend.current_time_la()

    # Fetch current time in australia
    aest = backend.current_time_aus()
    
    # Remove whitespace
    argument = ''.join(argument.split())
    
    # If no argument, give all studio times
    if len(argument) < 1:
        output = (
            "The current time in Toronto is: " + est + "\nThe current time in Montreal is: " +
            est + "\nThe current time in Boston is: " + est + "\nThe current time in Stockholm is: " + cest +"\nThe current time in Los Angeles is: "+pdt + "\nThe current time in Sydney is: "+aest
        )
    else:
        argument = argument.lower()
        output = 'Please Enter a valid Studio or Location'
        
        if argument in ["tor", "toronto"]:
            output = "The current time in Toronto is: " + est
        elif argument in ["mtl", "montreal"]:
            output = "The current time in Montreal is: " + est
        elif argument in ["boston", "bos", "zero"]:
            output = "The current time in Boston is: " + est
        elif argument in [ "stk", "sth", "stockholm"]:
            output = "The current time in Stockholm is: " + cest
        elif argument in ["la","los angeles", "hollywood", "cali", "california"]:
            output = "The current time in Los Angeles is: "+pdt
        elif argument in ["aus", "sydney", "australia", "queensland", "the land down under"]:
            output = "The current time in Sydney is: "+aest

    try:
        # client.chat_postEphemeral(
        #     channel=channel_id,
        #     user=user_id,
        say(
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": output},
                }
            ],
            text=output
        )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="An error occurred, please enter a valid studio"
        )

"""
Repository of all commands in DreamBot.
"""
@app.command("/commands")
def commands(ack, logger, command, client):
    ack()
    user_id = command["user_id"]
    channel_id = command["channel_id"]

    output = (
        "/command\n\n"
        "For more information about dreambot visit: link to confluence page (redacted) \n\n"
        "/911 (message): Sends a 911 OpsGenie alert out with the included message (only for genuine emergencies)\n\n"
        "/breach (message): Sends an OpsGenie breach alert out with the enclosed message (only to be used in the event of a data or security breach)\n\n"
        "/due: Displays the tasks due in the next week\n\n"
        "/links: Displays links to company webpages\n\n"
        "/mixtape: Returns the latest Mixtape Monday\n\n"
        "/myrender: Displays render progress of the caller\n\n"
        "/renders: displays all currently running render jobs\n\n"
        "/renderstatus (argument): Renderstatus followed by either a showcode (e.g., for a shot ANDOR-103-240, ANDOR will work with this command) or a username displays the render progress associated with either that user or the show\n\n"
        "/rollcall (argument): Followed by a department, it displays all of the active users associated with said department\n\n"
        "/studiotime (argument): Displays the current time at that studio. If the argument is null, it displays all studio times\n\n"
        "/today: Displays the tasks due today\n\n"
        "/whoasset (username): Returns all hardware assets checked out by the username in the argument field\n\n"
        "/whohou: Displays the current Houdini license status\n\n"
        "/whonuke: Displays the current Nuke license status\n\n"
        "/workstation: Displays the workstation of the caller\n\n"
    )
    
    try:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": output},
                }
            ],
            text=output
        )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"An error occurred: {e}"
        )

"""
Displays the workstation number of the caller.
"""
@app.command("/workstation")
def workstation(ack, logger, command, client):
    # Acknowledge the slash command request
    ack()

    # Get user ID who triggered the command
    user_id = command["user_id"]
    channel_id = command["channel_id"]

    try:
        # Call the Slack API to get user info including email
        response = client.users_info(user=user_id)
        
        # Extract user email from response
        user_email = response["user"]["profile"]["email"]
        holder = user_email.split("@")
        username = holder[0]
        
        # Execute the bash command
        user_command = f'whoasset {username}'
        result = subprocess.run(['bash', '-c', user_command], capture_output=True, text=True)
        output = result.stdout.strip()
    
        # Post an ephemeral message back to the user
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": output},
                }
            ],
            text=output
        )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"An error occurred: {e}"
        )


def formatArraysWeek(ahri):
    """
    Formats the due tasks for the week into a table for Slack.
    """
    shop = ""
    shop += "```"
    
    header = "{:<8s} {:<25s} {:<10s} {:<10s}".format("Project", "Task Assignees", "Step", "Due")
    shop += f"{header}\n"
    
    # Adjusting the separator line to match the total width
    shop += "-" * 60 + "\n"
    
    # Indexing through each day's due tasks
    for block in ahri:
        
        # Indexing through the tasks themselves and formatting
        for item in block:
            try:
                project = str(item[1])[:3]
                task_assignees = str(item[2])[:25]
                step = str(item[4])[:10]
                end = str(item[5])[:10]

                row = "{:<8s} {:<25s} {:<10s} {:<10s}".format(project, task_assignees, step, end)
                shop += f"{row}\n"
            except:
                # In case there is a day with no tasks
                continue 

    shop += "```"
    return shop


def formatArrays(ahri):
    """
    Formats the due tasks for the day into a table for Slack.
    """
    shop = ""
    shop += "```"
    
    header = "{:<8s} {:<25s} {:<10s} {:<10s}".format("Project", "Task Assignees", "Step", "Due")
    shop += f"{header}\n"
    
    # Adjusting the separator line to match the total width
    shop += "-" * 60 + "\n"
    
    # Indexing through each task
    for item in ahri:
        try:
            project = str(item[1])[:3]
            task_assignees = str(item[2])[:25]
            step = str(item[4])[:10]
            end = str(item[5])[:10]

            row = "{:<8s} {:<25s} {:<10s} {:<10s}".format(project, task_assignees, step, end)
            shop += f"{row}\n"
        except:
            continue

    shop += "```"
    return shop


def formatRoles(role):
    """
    Formats the rolecall command into a table.
    Called by both rolecall department and rollcall showcode.
    """
    shop = ""
    
    header = "{:<15s} {:<30s} {:<30s}".format("Name", "Email", "Job Title")
    shop += f"{header}\n"
    
    # Adjusting the separator line to match the total width of 80 characters
    shop += "-" * 80 + "\n"
    
    # Indexing through each task
    for item in role:
        try:
            name = str(item[0])[:15]  # Accessing dictionary keys
            email = str(item[1])[:30]
            if item[2] is not None:
                rmSlash = item[2].split("/")
                title = str(rmSlash[0])[:30]
            else:
                title = "None"

            row = "{:<15s} {:<30s} {:<30s}".format(name, email, title)
            shop += f"{row}\n"
        except KeyError as e:
            # Debugging info for missing keys
            print(f"Missing key: {e}")
            continue
    return shop


def get_today_deliveries():
    """
    Gets the deliveries for the day.
    """
    today_final = backend.getTasksDue("Final Delivery", backend.to_day())
    today_final = formatArrays(today_final)
    
    return (f"*FINAL delivery {backend.humanReadable(backend.to_day())}:*\n"
            f"{today_final}")


def get_deliveries_text():
    """
    Provides the deliveries for the next week.
    """
    today_final = []
    today_final.append(backend.getTasksDue("Final Delivery", backend.to_day()))
    
    # Number determines the days it goes until (set to a week right now)
    x = 1
    while x < 7:
        today_final.append(backend.getTasksDue("Final Delivery", backend.dayAdder(x)))
        x += 1
    
    today_final = formatArraysWeek(today_final)

    return (f"*FINAL delivery Week from {backend.humanReadable(backend.to_day())}:*\n"
            f"{today_final}")


def get_whohou_text():
    """
    Calls and processes the whohou command line argument.
    """
    result = subprocess.run(['bash', '-c', 'whohou less'], capture_output=True, text=True)
    output = result.stdout.strip()
    lines = output.split('\n')

    formatted_output = "*Houdini Licenses:*\n"
    formatted_output += "```"
    
    for line in lines:
        formatted_output += f"\n{line}"
    
    formatted_output += "\n```"

    return formatted_output


def get_nuke_text():
    """
    Pulls the data from whonuke and formats it into a table fit for Slack.
    """
    result = subprocess.run(['bash', '-c', 'whonuke less'], capture_output=True, text=True)
    output = result.stdout.strip()

    # Split by /n, then manage first 3 rows
    lines = output.splitlines()
    output = "*Nuke Licenses:* \n"
    output += "```" 
    output += lines[0] + "\n\n" + lines[2] + "\n" + lines[3] + "\n\n"
    
    row = lines[5].split()
    squirtle = "{:<20s} {:<15s} {:<7s} {:<13s} {:<20s}".format(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]))
    output += squirtle + "\n"
    
    row = lines[6].split()
    bulbusaur = "-------------        ----------      ----------------     ------------"
    output += bulbusaur + "\n"
    
    x = 7
    while x < len(lines):
        rows = lines[x].split()
        charmander = "{:<20s} {:<15s} {:<20s} {:<20s}".format(str(rows[0]), str(rows[1]), str(rows[2]), str(rows[3]))
        output += "\n" + charmander
        x += 1
    
    output += "\n```" 
    return output 


def getJobDetails(job_id):
    """
    Returns the job on the render farm based on the show name associated with the job.
    """
    return deadcon.Jobs.GetJobDetails(job_id)[job_id]


def job_by_name(job_name):
    """
    Returns the job on the render farm based upon the show name associated with the job.
    """
    active_jobs = deadcon.Jobs.GetJobsInState("Active")
    output = str('\nShowing job details for: ' + str(job_name) + '\n\n')
    job_found = False
    
    for job in active_jobs:
        job_details = getJobDetails(job['_id'])['Job']
        storage = job_details['Name'].split("_")
        storage = storage[0].split("-")
        namey = storage[0]
        if namey == job_name:
            job_found = True
            job_id = job['_id']
            output += (
                'JOB NAME: ' + job_details['Name'] + '\n' +
                'JOB ID: ' + job_id + '\n' +
                'USER: ' + job_details['User'] + '\n' +
                'SUBMITTED AT: ' + job_details['Submit Date'] + '\n' +
                'RUNNING TIME: ' + getJobDetails(job_id)['Statistics']['Running Time'] + '\n' +
                'PROGRESS: ' + job_details['Progress'] + '\n-------------------------------\n'
            )
    
    if not job_found:
        output += 'No jobs found with the name: ' + str(job_name) + '\n'
    
    return output

def all_jobs():
    """
    Returns all active jobs on the render farm
    """
    active_jobs = deadcon.Jobs.GetJobsInState("Active")
    output = str('\n/Renders: Showing all currently active jobs\n\n')
    for job in active_jobs:
        job_details = getJobDetails(job['_id'])['Job']
        job_id = job['_id']
        output += (
            'JOB NAME: ' + job_details['Name'] + '\n' +
            'JOB ID: ' + job_id + '\n' +
            'USER: ' + job_details['User'] + '\n' +
            'PROGRESS: ' + job_details['Progress'] + '\n-------------------------------\n'
        )
    return output

def user(username):
    """
    Gives all render jobs associated with a username.
    """
    username = username.lower()
    users_jobs = deadcon.Jobs.GetJobsInState("Active")
    output = str('\nShowing all jobs submitted by: ' + str(username) + '\n\n')
    active_job = False
    
    for job in users_jobs:
        if str(job['Props']['User']) == username:
            active_job = True
            job_id = job['_id']
            job_details = getJobDetails(job_id)['Job']
            output += (
                'JOB NAME: ' + job_details['Name'] + '\n' +
                'JOB ID: ' + job_id + '\n' +
                'SUBMITTED AT: ' + job_details['Submit Date'] + '\n' +
                'RUNNING TIME: ' + getJobDetails(job_id)['Statistics']['Running Time'] + '\n' +
                'PROGRESS: ' + job_details['Progress'] + '\n\n'
            )

    if (active_job == False):
        output += 'No jobs submitted by: ' + str(username) + '\n'
    
    return output



if __name__ == "__main__":
    SocketModeHandler(app, str(constants.xapp)).start()
