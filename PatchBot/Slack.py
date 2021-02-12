#!/usr/bin/env python3

# Slack.py v1.0
# Ryon Riley 11/01/2021
#

"""See docstring for Slack class"""

import json
import plistlib
import os.path as path
import datetime
import logging
import logging.handlers
import sys
import requests

__all__ = ["Slack"]

# logging requirements
LOGFILE = "/usr/local/var/log/Slack.log"
LOGLEVEL = logging.INFO


class Slack:
    """When given the location of an output plist from Autopkg parses it
    and sends the details on packages uploaded to Jamf Pro to Slack
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
        # URL for a button to open package test policy in Jamf Pro
        self.pol_base = "https://advisorytest.jamfcloud.com/policies.html?id="

        # set up logging
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        frmt = "%(levelname)s {} %(message)s".format(now)
        # set up logging
        logging.basicConfig(filename=LOGFILE, level=LOGLEVEL, format=frmt)
        self.logger = logging.getLogger("")
        # set logging formatting
        # ch = logging.StreamHandler()
        ch = logging.handlers.TimedRotatingFileHandler(
            LOGFILE, when="D", interval=1, backupCount=7
        )
        ch.setFormatter(logging.Formatter(frmt))
        self.logger.addHandler(ch)
        self.logger.setLevel(LOGLEVEL)

        # JSON for the message to Slack
        # "sections" will be replaced by our work
        self.template = """
        {
        "username": "PatchBot",
        "icon_emoji": ":patchbot:",
        "channel": "#patchbotlogging",
        "text": "Packages uploaded",
        "attachments": [
            ]
        }
        """

        # JSON for a section of a message
        # we will have a section for each package uploaded
        # in this Autopkg run
        self.attachment = """
        {
            "startGoup": "true", "title": "**AppName**", "text": "version",
            "actions": [
                {
                    "name": "Policy",
                    "type": "button",
                    "value": "policy",
                    "url": [

                        ]
                    ]
                }
            ]
        }
        """

        # JSON template for the error message card.
        self.err_template = """
        {
        "username": "PatchBot",
        "icon_emoji": ":patchbot:",
        "channel": "#patchbotlogging",
        "text": "Package errors",
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

        # JSON template for the empty run message card.
        self.none_template = """
        {
        "username": "PatchBot",
        "icon_emoji": ":patchbot:",
        "channel": "#patchbotlogging",
        "text": "**Empty run**",
        "attachments": [
            ]
        }
        """

    def Slack(self):
        """Do the packages uploaded!"""
        self.logger.info("Starting Run")
        attachments = []
        empty = False
        jsr = "jpc_importer_summary_result"
        try:
            fp = open(self.plist, "rb")
            pl = plistlib.load(fp)
        except IOError:
            self.logger.error("Failed to load %s", self.plist)
            sys.exit()
        item = 0
        if jsr not in pl["summary_results"]:
            self.logger.debug("No JPCImporter results")
            empty = True
        else:
            for p in pl["summary_results"][jsr]["data_rows"]:
                attachments.append(json.loads(self.attachment))
                # get the package name without the '.pkg' at the end
                pkg_name = path.basename(p["pkg_path"])[:-4]
                pol_id = p["policy_id"]
                self.logger.debug("Policy: %s Name: %s", pol_id, pkg_name)
                (app, version) = pkg_name.split("-")
                pol_uri = self.pol_base + pol_id
                attachments[item]["title"] = "**%s**" % app
                attachments[item]["text"] = version
                attachments[item]["actions"][0]["url"][0][
                    "uri"
                ] = pol_uri
                item = item + 1
            j = json.loads(self.template)
            j["attachments"] = attachments
            d = json.dumps(j)
            headers = {'Content-Type': "application/json"}
            requests.post(self.url, data=d, headers=headers)
        # do the error messages
        fails = pl["failures"]
        if len(fails) == 0:  # no failures
            if empty:  # no failures and no summary so send empty run message
                headers = {'Content-Type': "application/json"}
                requests.post(self.url, data=self.none_template, headers=headers)
            sys.exit()
        attachments = []
        item = 0
        for f in fails:
            attachments.append(json.loads(self.err_section))
            attachments[item]["title"] = "**%s**" % f["recipe"]
            attachments[item]["text"] = f["message"].replace("\n", " ")
            item = item + 1
        j = json.loads(self.err_template)
        j["attachments"] = attachments
        d = json.dumps(j)
        headers = {'Content-Type': "application/json"}
        requests.post(self.url, data=d, headers=headers)


if __name__ == "__main__":
    Slack = Slack()
    Slack.Slack()
