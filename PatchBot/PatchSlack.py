#!/usr/bin/env python3

# PatchTeams.py v1.0b
# Tony Williams 25/07/2019
#

"""See docstring for PatchSlack class"""

import json
import plistlib
import os.path as path
import datetime
import logging
import logging.handlers
import sys
import requests

__all__ = ["PatchSlack"]

# logging requirements
LOGFILE = "/usr/local/var/log/PatchSlack.log"
LOGLEVEL = logging.DEBUG


class PatchSlack:
    """When given the location of an output plist from Autopkg parses it
    and sends the details on packages productionized to Jamf Pro to Slack
    """

    description = __doc__

    def __init__(self):

        # extremely dumb command line processing
        try:
            self.plist = sys.argv[1]
        except IndexError:
            self.plist = "autopkg.plist"

        # URL of Slack webhook
        self.url = "https://hooks.slack.com/services/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"

        # set up logging
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        frmt = "%(levelname)s {} %(message)s".format(now)
        # set up logging
        logging.basicConfig(filename=LOGFILE, level=LOGLEVEL, format=frmt)
        self.logger = logging.getLogger("")
        # set logging formatting
        # ch = logging.StreamHandler()
        ch = logging.handlers.TimedRotatingFileHandler(
            LOGFILE, when="D", interval=7, backupCount=4
        )
        ch.setFormatter(logging.Formatter(frmt))
        self.logger.addHandler(ch)
        self.logger.setLevel(LOGLEVEL)

        # JSON for the message to Slack
        # "attachments" will be replaced by our work
 
        # self.template = """
        # {
        # "username": "PatchBot",
        # "icon_emoji": ":patchbot:",
        # "channel": "#patchbotlogging",
        # "text": "Patch Manager",
        # "attachments": [
		#     ]
        # }
        # """

        self.template = {
            "username": "PatchBot",
            "icon_emoji": ":patchbot:",
            "channel": "#patchbotlogging",
            "text": "Patch Manager",
            "attachments": []
        }


        # JSON for a  of a message
        # we will have a section for each package uploaded
        # in this Autopkg run
        # (It looks ugly to keep pylint happy)
        self.attachment = """
        {"startGoup": "true", "patch_id": "**AppName**", "text": "version"
        }
        """

        # JSON template for the error message card.
        self.err_template = """
        {
        "username": "PatchBot",
        "icon_emoji": ":patchbot:",
        "channel": "#patchbotlogging",
        "text": "Patch management errors",
        "attachments": [
		    ]
        }
        """

        # JSON template for a single error on error card.
        self.err_section = """
        {
            "text": "A long message",
            "startGoup": "true",
            "title": "**Firefox.pkg**"
        }
        """

        # JSON template for the error message card.
        # self.none_template = """
        # {
        # "username": "PatchBot",
        # "icon_emoji": ":patchbot:",
        # "channel": "#patchbotlogging",
        # "text": "**Empty run**",
        # "attachments": [
		#     ]
        # }
        # """

        self.none_template = {
            "username": "PatchBot",
            "icon_emoji": ":patchbot:",
            "channel": "#patchbotlogging",
            "text": "**Empty run**",
            "attachments": []
        }



    def PatchSlack(self):
        """Do the patches changed!"""

        self.logger.info("Starting Run for PatchSlack() function")

        attachments = []

        empty = False
        jsr = "patch_manager_summary_result"

        try:
            fp = open(self.plist, "rb")
            pl = plistlib.load(fp)
        except IOError:
            self.logger.error("Failed to load %s", self.plist)
            sys.exit()
        item = 0

        if jsr not in pl["summary_results"]:
            self.logger.debug("No Patch results")
            empty = True
        else:
            pkgs = pl["summary_results"][jsr]["data_rows"]
            for p in pkgs:
                attachments.append(json.loads(self.attachment))
                name = p["patch_id"]
                version = p["version"]
                self.logger.debug("Version: %s Name: %s", version, name)
                attachments[item]["patch_id"] = "**%s**" % name
                attachments[item]["text"] = version
                item = item + 1
    
            ## Switched to storing json in the variable, rather than using
            ## json.loads and json.dumps.

            # j = json.loads(self.template)

            j = self.template
            j["attachments"] = attachments

            # d = json.dumps(j)
            d = j
            headers = {'Content-Type': "application/json"}

            ## Instead of using "data=" we're going to use "json=" because
            ## requests has a "json" option to send json data through POST

            # requests.post(self.url, data=d, headers=headers)
            requests.post(self.url, json=d, headers=headers)

        # do the error messages
        fails = pl["failures"]
        if len(fails) == 0:  # no failures
            if empty:
                headers = {'Content-Type': "application/json"}

                ## Instead of using "data=" we're going to use "json=" because
                ## requests has a "json" option to send json data through POST

                # requests.post(self.url, data=self.none_template, headers=headers)

                requests.post(self.url, json=self.none_template, headers=headers)
            sys.exit()

        attachments = []

        item = 0
        for f in fails:
            attachments.append(json.loads(self.err_section))
            attachments[item]["title"] = "**%s**" % f["recipe"]
            attachments[item]["text"] = f["message"].replace("\n", " ")
            item = item + 1

        # j = json.loads(self.err_template)
        j = self.err_template

        j["attachments"] = attachments
        # d = json.dumps(j)
        d = j
        headers = {'Content-Type': "application/json"}
        # requests.post(self.url, data=d, headers=headers)
        requests.post(self.url, json=d, headers=headers)


if __name__ == "__main__":
    PatchSlack = PatchSlack()
    PatchSlack.PatchSlack()
