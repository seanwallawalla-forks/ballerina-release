from json import dumps
from cryptography.fernet import Fernet
from httplib2 import Http
from github import Github
import os
import sys
import csv
import constants
import notify_chat

def main():
    ballerina_bot_token = os.environ[constants.ENV_BALLERINA_BOT_TOKEN]
    github = Github(ballerina_bot_token)
    repo = github.get_repo(constants.BALLERINA_ORG_NAME + '/' + sys.argv[1])
    code_owner_content = repo.get_contents('.github/CODEOWNERS')
    owners = code_owner_content.decoded_content.decode().split("*")[1].split("@")
    encryption_key = os.environ['ENV_USER_ENCRYPTION_KEY']

    fernet = Fernet(encryption_key)
    with open('dependabot/resources/github_users_encrypted.csv', 'rb') as enc_file:
        encrypted_csv = enc_file.read()

    decrypted = fernet.decrypt(encrypted_csv)
    with open('dependabot/resources/github_users_decrypted.csv', 'wb') as dec_file:
        dec_file.write(decrypted)

    message = "*" + str(sys.argv[1]) + "* daily build failure" + "\n" +\
              "Please visit <https://github.com/ballerina-platform/" + str(sys.argv[1]) + "/actions?query=workflow%3A%22Daily+build%22|the daily build page> for more information" +"\n"

    for owner in owners :
        with open('dependabot/resources/github_users_decrypted.csv', 'r') as read_obj:
            user_file = csv.DictReader(read_obj)
            owner = owner.strip()
            for row in user_file:
                if row['gh-username'] == owner:
                    message += "<users/" + row['user-id'] + ">" + "\n"

    notify_chat.send_message(message)

main()
