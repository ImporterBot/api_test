#!/usr/bin/env python
#
# Lara Maia <dev@lara.click> 2017
#
# This file is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#

import argparse
import codecs
import configparser
import locale
import logging
import os
import requests
import sys
import time


def encoder(buffer, error='replace'):
    writer = codecs.getwriter(locale.getpreferredencoding())
    return writer(buffer, error)


def multiline_input(information):
	print(information)
	print('(Write :wq to process)')
	
	text = []
	while True:
		user_input = input()
		if user_input == ':wq':
			break
		else:
			text.append(user_input)

	return '\n'.join(text)


def get_issue_data(issue):
	response = requests.get(
		'{}/repos/{}/{}/issues/{}'.format(
			api_server,
	        account,
	        repository,
	        issue
	    )
	)

	return response.json()

def send_data(title, user, date, body, issue=None):
	post_url = "/repos/{}/{}/issues".format(account, repository)
	
	if issue is not None:
		post_url += '/{}'.format(issue)

	data = {'title': title,
			'body': '> :bust_in_silhouette: From: {}'.format(user)+
			'\n> :calendar: At: {}'.format(date)+
			'\n> ---\n{}'.format(body)}
			
	headers = {'Authorization': 'token ' + auth_token}

	logger.debug('\n\nSending to: %s', api_server + post_url)
	logger.debug('With: %s', data)

	response = requests.post(api_server + post_url, json=data, headers=headers)

	logger.info('\nServer response: %s', response.status_code)
	logger.info('Your issue is at: %s', response.json()['url'])
	
	return None


if __name__ == '__main__':
	logger = logging.getLogger('Github API Helper')
	logger.setLevel(logging.DEBUG)
	console = logging.StreamHandler(encoder(sys.stdout.buffer))
	console.setLevel(logging.INFO)
	logger.addHandler(console)
	
	config_parser = configparser.RawConfigParser()
	config_parser.optionxform = str
	
	if not os.path.isfile('config.ini'):
		logger.error("No config file found.")
		sys.exit(1)

	config_parser.read('config.ini')
	api_server = config_parser.get('Config', 'apiServer')
	account = config_parser.get('Config', 'account')
	repository = config_parser.get('Config', 'repository')
	auth_token = config_parser.get('Config', 'authToken')


	command_parser = argparse.ArgumentParser()

	single = command_parser.add_mutually_exclusive_group()
	single.add_argument('-c', '--create', action='store_true', help='Create an issue')
	single.add_argument('-e', '--edit', metavar='issue', help='Edit an issue')

	command_params = command_parser.parse_args()

	if command_params.create:
		logger.info('-- Creating a new issue')
		title = input('Title: ')
		user = input('User: ')
		date = input('Date: ')
		body = multiline_input('Body: ')
		send_data(title, user, data, body)
	elif command_params.edit:
		issue = command_params.edit

		logger.info('-- Editing issue %s', issue)

		issue_data = get_issue_data(issue)
		
		if issue_data['user']['login'] != "ImporterBot":
			logging.error('This issue is not created by ImporterBot')
			sys.exit(1)

		title = issue_data['title']
		user = issue_data['body'].split('\n')[0][29:]
		date = issue_data['body'].split('\n')[1][17:]
		body = issue_data['body'].split('\n')[3]
		logger.info('\n%s\n-\n%s\n%s\n-\n%s\n', title, user, date, body)

		while True:
			user_choose = input('   > Choose: [title/user/date/body/save/quit] ')
			logger.debug('User choose %s', user_choose)
			
			if user_choose == 'title':
				title = input('New title: ')
			elif user_choose == 'user':
				user = input('New user: ')
			elif user_choose == 'date':
				date = input('New date: ')
				if date == 'current':
					date = time.strftime("%d/%m/%Y")
					logger.info('Date defined to %s', date)
			elif user_choose == 'body':
				body = multiline_input('New body: ')
			elif user_choose == 'save':
				send_data(title, user, date, body, issue)
				break
			elif user_choose == 'quit':
				break
			else:
				logger.error('Please. Select an valid option.')
	else:
		command_parser.print_help()

	logger.info('Done')
	sys.exit(0)
