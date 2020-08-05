#!/usr/bin/python3

# Author: Haraldo Albergaria
# Date  : Jul 29, 2020
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


import flickrapi
import api_credentials
import json
import time
import os
import sys


#===== CONSTANTS =================================#

api_key = api_credentials.api_key
api_secret = api_credentials.api_secret
user_id = api_credentials.user_id

group_url = "https://www.flickr.com/groups/the-map-group/"
photos_url = "http://www.flickr.com/photos"
map_group_url = "https://the-map-group.pictures"

# Flickr api access
flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

# get full script's path
repo_path = os.path.dirname(os.path.realpath(__file__))
groups_path = repo_path + "/groups"
people_path = repo_path + "/people"


#===== MAIN CODE ==============================================================#

# get group id and name from group url
group_id = flickr.urls.lookupGroup(api_key=api_key, url=group_url)['group']['id']
group_name = flickr.groups.getInfo(group_id=group_id)['group']['name']['_content']

# get members from group
members = flickr.groups.members.getList(api_key=api_key, group_id=group_id)
total_of_members = int(members['members']['total'])
number_of_pages  = int(members['members']['pages'])
members_per_page = int(members['members']['perpage'])

# iterate over each members page
for page_number in range(number_of_pages, 0, -1):
    members = flickr.groups.members.getList(api_key=api_key, group_id=group_id, page=page_number, per_page=members_per_page)['members']['member']
    # iterate over each member in page
    for member_number in range(len(members)-1, -1, -1):
        try:
            member_name = members[member_number]['username']
            member_id = members[member_number]['nsid']
            member_alias = flickr.people.getInfo(api_key=api_key, user_id=member_id)['person']['path_alias']
            if member_alias == None:
                member_alias = member_id
            member_path = people_path + "/" + member_alias
            # create member directory and topic if doesn't exist yet
            is_new_member = False
            if not os.path.isdir(member_path):
                command = "{0}/setup-member.sh {1}".format(people_path, member_alias)
                os.system(command)
                is_new_member = True
            # generate/update member's map
            command = "{}/generate-map.py".format(member_path)
            os.system(command)
            if os.path.exists("{}/map.html".format(member_path)) and os.path.exists("{}/statcounter".format(member_path)):
                map_file = open("{}/map.html".format(member_path))
                map = map_file.readlines()
                map_file.close()
                stats_file = open("{}/statcounter".format(member_path))
                stats = stats_file.readlines()
                stats_file.close()
                index_file = open("{}/index.html".format(member_path), 'w')
            else:
                sys.exit()

            for map_line in map:
                if map_line == "</body>\n":
                    for stats_line in stats:
                        index_file.write(stats_line)
                    index_file.write('\n')
                index_file.write(map_line)
            index_file.close()

            # upload map
            os.system("cp {0}/favicon.ico {1}".format(repo_path, member_path))
            os.system("git add -f {}/index.html".format(member_path))
            os.system("git add -f {}/favicon.ico".format(member_path))
            os.system("git commit -m \"Updated map for member \'{}\'\"".format(member_name))
            os.system("git push origin master")
            print('Uploaded map')
            os.system("rm {}/index.html".format(member_path))
            os.system("rm {}/favicon.ico".format(member_path))
            os.system("rm {}/map.html".format(member_path))
            os.system("rm -fr {}/__pycache__".format(member_path))
            if is_new_member:
                topic_subject = "[MAP] {}".format(member_name)
                member_map = "{0}/people/{1}/".format(map_group_url, member_alias)
                topic_message = "[{0}/{1}/] Map link: <a href=\"{3}\"><b>{3}</b></a>\n\nClick on the markers to see the photos taken on the corresponding location.".format(photos_url, member_alias, member_name, member_map)
                flickr.groups.discuss.topics.add(api_key=api_key, group_id=group_id, subject=topic_subject, message=topic_message)
                print('Created discussion topic for new member')

        except:
            pass

