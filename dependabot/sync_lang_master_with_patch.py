import os
import sys
import time

from github import Github

import constants
import notify_chat

PULL_REQUEST_TITLE = '[Automated] Merge patch branch with the master'

SLEEP_INTERVAL = 30 # 30s
MAX_WAIT_CYCLES = 180 # script timeout is 90 minutes

ballerina_bot_token = os.environ[constants.ENV_BALLERINA_BOT_TOKEN]
ballerina_reviewer_bot_token = os.environ[constants.ENV_BALLERINA_REVIEWER_BOT_TOKEN]
github = Github(ballerina_bot_token)

def main():
    repo = github.get_repo(constants.BALLERINA_ORG_NAME + '/' + 'ballerina-lang')
    branches = repo.get_branches()

    for branch in branches:
        if (branch.name == '2201.0.x'):
            patch_branch = branch.name
            break

    # Check whether master branch already has an unmerged PR from patch branch
    pr_exists = False
    pulls = repo.get_pulls(state='open')
    for pull in pulls:
        if (pull.head.ref == patch_branch):
            pr_exists = True
            unmerged_pr = pull

    if (pr_exists):
        print ("Master branch already has an open pull request from " + patch_branch)
        unmerged_pr.edit(state = 'closed')

    pr = create_pull_request(repo, patch_branch)

    pending = True
    wait_cycles = 0
    while pending:
        if wait_cycles < MAX_WAIT_CYCLES:
            time.sleep(SLEEP_INTERVAL)
            pending, passing = check_pending_pr_checks(repo, pr)
            if not pending:
                if passing:
                    if(pr.mergeable):
                        try:
                            pr.merge()
                            log_message = "[Info] Automated master update PR merged. PR: " + pr.html_url
                            print(log_message)
                        except Exception as e:
                            print("[Error] Error occurred while merging master update PR " , e)
                    else:
                        notify_chat.send_message("[Info] Automated ballerina-lang master update PR is unmerged due to conflicts with the master." + "\n" +\
                                "Please visit <" + pr.html_url + "|the build page> for more information")
                else:
                    notify_chat.send_message("[Info] Automated ballerina-lang master update PR has failed checks." + "\n" +\
                     "Please visit <" + pr.html_url + "|the build page> for more information")
            else:
                wait_cycles += 1
        else:
            notify_chat.send_message("[Info] Automated ballerina-lang master update PR is unmerged due to pr checks timeout." + "\n" +\
             "Please visit <" + pr.html_url + "|the build page> for more information")
            break

def create_pull_request(repo, patch_branch):
    try:
        pull_request_title = PULL_REQUEST_TITLE
        created_pr = repo.create_pull(
            title=pull_request_title,
            body='Daily syncing of patch branch content with the master',
            head=patch_branch,
            base=repo.default_branch
        )
        log_message = "[Info] Automated PR created for ballerina-lang repo at " + created_pr.html_url
        print(log_message)
    except Exception as e:
        print("[Error] Error occurred while creating pull request ", e)
        sys.exit(1)

    try:
        approve_pr(created_pr.number)
    except Exception as e:
        print("[Error] Error occurred while approving the PR ", e)
    return created_pr

def approve_pr(pr_number):
    time.sleep(5)
    r_github = Github(ballerina_reviewer_bot_token)
    repo = r_github.get_repo(constants.BALLERINA_ORG_NAME + '/ballerina-lang')
    pr = repo.get_pull(pr_number)
    try:
        pr.create_review(event='APPROVE')
        print(
            "[Info] Automated master update PR approved. PR: " + pr.html_url)
    except Exception as e:
        raise e

def check_pending_pr_checks(repo, pr):
    print("[Info] Checking the status of the dependency master syncing PR ")
    passing = True
    pending = False
    pull_request = repo.get_pull(pr.number)
    sha = pull_request.head.sha
    for pr_check in repo.get_commit(sha=sha).get_check_runs():
        if pr_check.status != 'completed':
            pending = True
            break
        elif pr_check.conclusion == 'success':
            continue
        else:
            passing = False
    return pending, passing

main()
