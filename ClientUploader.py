#!/usr/bin/python
import os
import socket
import requests
import json
import base64
import time
import textwrap
import pprint as pp
import sys
from CONSTANTS import *
from colorama import init, Fore, Style

init(convert=True)

# TODO: Use networking to report Exceptions to the discord client?


class Imgur:
    PROFILE = "DiscordPictureWizard" # chances are this won't ever have to change but I'd hate to hardcode it
    header = {'authorization': 'Client-ID ' + CLIENT_ID}
    auth_header = {'authorization': 'Bearer ' + ACCESS_TOKEN}
    albums = {}
    album_data = {}

    def post_album(self):
        current_album_id = None
        try:
            if not Files.media_array:
                print("No pictures to upload.")
                return
            if list(self.album_data.keys())[0] == Files.album_name:
                print("-------------Uploading Files-------------")
                print("\n" + "Existing album of the same name found in Imgur.")
                data = self.album_data[Files.album_name]
                for k,v in self.album_data[Files.album_name].items():
                    if k == 'id':
                        current_album_id = v
                        break
                    if k != 'id' and k == len(data):
                        Files.displayError("There was a problem accessing the file on Imgur")
                        return
                    else:
                        continue
        except IndexError:
            # really shitty way of doing this but out of index error = no album and I don't wanna bother rewriting code
            # maybe once I started getting paid for it
            print("No album named " + Files.album_name + " was found.\n")
            print("Creating new album named " + Files.album_name + "\n ")
            data = {'title': Files.album_name}
            r = requests.post('https://api.imgur.com/3/album', data=data, headers=self.auth_header)
            rjson = r.json()
            self.album_data[Files.album_name] = rjson['data']
            time.sleep(1)
            Imgur().post_album()


        else:
            x = requests.get('https://api.imgur.com/3/album/' + current_album_id + '/images', headers=self.header)
            xjson = json.loads(x.text)

            # checking if GET request was successful
            pp.PrettyPrinter(indent=4)
            for k, v in xjson.items():
                if k == 'success':
                    if v == True:
                        break
                    else:
                        Files.displayError("There was a problem accessing the Album. Printing JSON response.")

            print("\n" + "Files shown in" + Fore.GREEN + " green " + Style.RESET_ALL + "will be uploaded.")
            print("Files shown in"+ Fore.RED + " red " + Style.RESET_ALL + "already exist in the album.")
            print(Fore.MAGENTA + "Duplicate " + Style.RESET_ALL + "files will only be uploaded once if they're not "
                "already" + Fore.RED + " red" + Style.RESET_ALL + "." + "\n")
            green_array = []
            red_array = []

            #might be a redundant looping over the same values again but I don't know how to check for the value of
            #two different things at the same time since the second loop would have to rely on success == true
            #and by that time k k might have iterated over the second value I wanted to check

            #looping over the ENTIRE json response and adding items with 'title' into a dictionary
            #TODO: parsing could be easier if it was a list instead
            iter_data = xjson['data']
            imgur_result = []
            for i in range(len(iter_data)):
                for name, value in iter_data[i].items():
                    if name == 'title':
                        imgur_result.append(value)

            for i, title in enumerate(Files.media_array):
            #don't bother checking anything if there's already nothing in the album
                if not xjson['data']:
                    green_array.append(title)
                    print(Fore.GREEN + title)
                    print(Style.RESET_ALL)
                    if i == len(Files.media_array):
                        break
                    continue

                #if there is, go over items in
                for x, v in enumerate(imgur_result):
                    if title in red_array:
                        print(Fore.MAGENTA + title)
                        print(Style.RESET_ALL)
                        break
                    elif title in green_array:
                        red_array.append(title)
                        print(Fore.MAGENTA + title)
                        print(Style.RESET_ALL)
                        break
                    for i in green_array: #if file has the name "- Copy" in it, don't upload
                        #TODO: only enter loop if element is in the end of the array, if not move it to the end
                        #it's possible that " - COPY" files are iterated before their original file so anything
                        #that is a copy gets checked last. If the original is there, upload it
                        #if not show the user that it found that it was a copy even tho the name was different.
                        if i == i + " - Copy" + os.path.splitext(title)[1]:
                            red_array.append(i)
                            print(Fore.MAGENTA + title)
                            print(Style.RESET_ALL)
                            break
                        if i == i + " - Copy" + os.path.splitext(title)[1]:
                            red_array.append(i)
                            print(Fore.MAGENTA + title)
                            print(Style.RESET_ALL)
                            break
                    else:
                        if v == title:
                            red_array.append(title)
                            print(Fore.RED + title)
                            print(Style.RESET_ALL)
                            break
                        elif v != title and x == len(imgur_result) -1:
                            green_array.append(title)
                            print(Fore.GREEN + title)
                            print(Style.RESET_ALL)
                            break

            print("Pictures ready to upload: " + str(len(green_array)))
            print("Pictures not uploading: " + str(len(red_array)))
            print("")

            if len(green_array) > 0:
                inputx = input("Press Enter to upload the files in green.\n")
                if inputx == 'quit':
                    Files.exit = True

                #uploading the files
                error_found = False
                for file in green_array:
                    print("Attempting to add " + file + " to album " + Files.album_name + "\n")
                    image = open(file, 'rb')
                    image_read = image.read()
                    binary_encode = base64.encodebytes(image_read)
                    image.close()
                    parameters = {
                        'image': binary_encode,
                        'album': current_album_id,
                        'title': file,
                        'type': os.path.splitext(file)[1]
                    }
                    r = requests.post('https://api.imgur.com/3/image', data=parameters, headers=self.auth_header)
                    rjson = json.loads(r.text)
                    pp.PrettyPrinter(indent=4)
                    for k, v in rjson.items():
                        if k == 'status':
                            if v == '429':
                                print("Maximum upload limit for IP reached, upload will automatically resume after 1 hour\n")
                                Files.wait_period(3600)
                        if k == 'success':
                            if v:
                                print("Successfully uploaded.\n\n")
                            else: 
                                Files.displayError("There was an error uploading this file. Printing JSON response:\n")
                                pp.pprint(rjson)
                                error_found = True
                        if k == len(rjson) and k != 'success':
                            Files.displayError("Unexpected error: Printing JSON response.\nIf you see this message you either "
                                  "fucked something up or Imgur API isn't working")
                            pp.pprint(rjson)
                            error_found = True
                if error_found:
                    print("Not all files were uploaded successfully.")
                else:
                    print("All files were uploaded successfully!")
            else:
                print("No new pictures found in folder.")

###############End post_album ##############

    def get_albums(self):
        print("-----Attempting to fetch album information from Imgur-----" + "\n")
        r = requests.get('https://api.imgur.com/3/account/DiscordPictureWizard/albums/', headers=self.auth_header)
        parse = json.loads(r.text)
        data = parse["data"]
        if parse['success'] == True:
            print("Success!")
            albums_title = []
            albums_id = []
            print("\n" + "Albums found:\n")
            for i,title in enumerate(d['title'] for d in data):
                albums_title.append(title)
                if title != Files.album_name:
                    print(title)
                else:
                    print(title + "    <- Current album")
                    Imgur.album_data[title] = (data[i])
            for i, id in enumerate(d['id'] for d in data):
                albums_id.append(id)
            global albums
            albums = dict(zip(albums_title,albums_id))
        else:
            Files.displayError("There's been a problem getting album data.")

    def check_album_exists(self):
        r = requests.get('https://api.imgur.com/3/account/'+ Imgur.PROFILE +'/albums/', headers=self.header)
        parse = json.loads(r.text)
        data = parse["data"]
        for i in data:
            if parse['success'] == True:
                print("successful x pie")
                print(data[0])
                Imgur.album_data[Files.album_name] = data[0]['id']
                print(Imgur.album_data)
                break
            elif not parse['success']:
                continue
            else:
                print(Files.album_name + " still not in Albums.")


class Network:
    serverIP = None
    try:
        clientIP = requests.get('http://ip.42.pl/raw').text
    except Exception as e:
        clientIP = "-not found-"
        print(e)


class Files(object):
    directory = os.getcwd()
    album_name = os.getcwd().rsplit('\\', 1)[-1]
    hostname = socket.gethostname()
    test_address = "C:\\Users\\Ali\\Desktop\\Pics\\Wallpaper\\test.jpg"
    media_found = 0
    media_array = []
    exit = False

    def list_items(self):
        t0 = time.time()
        filesize = 0
        print("---------------Listing items----------------\n")
        print("Items found:\n")
        for file in os.listdir(self.directory):
            if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".gif") or file.endswith(".jpeg") or \
                    file.endswith(".tiff"):
                self.media_array.append(file)
                filesize += int((os.stat(file).st_size)/1000)
                self.media_found += 1
                print(file.ljust(80) + "\t\t" + str((os.stat(file).st_size)/1000).ljust(8) +  " kB")

        if self.media_found == 0:
            print("|| No images were found in folder. ||")
        t1 = time.time()
        total = int(t1-t0)

        if len(str(filesize)) < 4:
            print("\n\nTotal file size: " + str(filesize) + " kilobytes." + "\n")
        elif len(str(filesize)) < 7:
            print("\n\nTotal file size: " + str(filesize/1000) + " megabytes.")
        elif filesize > 5000000:
            raise Exception("\n\nYour file size is over 5 gigabytes, cannot process images")
        elif len(str(filesize)) < 8:
            print("\n\nTotal file size: " + str(filesize / 1000000) + " gigabytes.")
        print("Files scanned in: " + str(total) + " seconds")
        print("Total pictures found: " + str(self.media_found) + "\n")

    @staticmethod
    def wait_period(start):
        for i in range(start, 0, -1):
            sys.stdout.write('\r Time left: ' + str(i) + " seconds.")
            sys.stdout.flush()
            time.sleep(1)
    @staticmethod
    def countdown(max_number, countdown_message):
        for n in range(max_number+1, 0, -1):
            print(countdown_message + "in " + str(n), end='\r', flush=True)
            time.sleep(1)

    @staticmethod
    def displayError(string):
        print(Fore.RED + string + "\n")
        print(Style.RESET_ALL)

def startup():
    print("\n" + "======= Imgur Uploader ======")
    print("Host: " + Files.hostname + "\n" + "IP: " + str(Network.clientIP) + "\n")
    print("Description:")
    print("1."+ textwrap.dedent("Pictures found in the same folder as the script is in will be automatically uploaded "
        "to imgur under an album the same name as the folder this script is in. If no such album exists, it "
        "is automatically created."))
    print("2."+ textwrap.dedent("Pictures in subfolders will be ignored."))
    print("3."+ textwrap.dedent("Avoid changing the names of the files once they're uploaded (even if they're random)"
        "as it will cause them to upload twice."))
    print("4." +textwrap.dedent("If you want to have a private folder that you don't want other people to edit "
        "make sure you have a unique folder name like 'mosti_memes' as the "
        "script uses folder names to determine the name of albums."))
    print("5."+ textwrap.dedent("If you've never uploaded pictures before but the script recognizes your folder"
        " name you're most likely uploading to a generic folder like 'funny' or 'pics' accessible by other people."))
    Files.displayError("6.The Imgur API is SLOW. Running the program, then trying to upload again after"
                       " a short time (< 20 seconds) will probably result in you uploading the file"
                       " twice before it's marked as uploaded.")

    print("\n"+"Running in folder:" + "\n" + Files.directory + "\n")
    print("Album name:" + "\n" + Files.album_name + "\n")
    Files().list_items()
    Imgur().get_albums()
    print("\n" + "Commands:"+ "\n")
    print("\'upload\': Uploads all files in current folder to Imgur with the folder name as the album name.")
    print("\'albums\': Gets all album information from Imgur.")
    print("\'exit\': Exits the program... Same as clicking the close button at the top, idk why anyone would use this")
    print("Checking the contents of an album is not possible here, use the discord bot instead.")

def listener():
    command =input("\nEnter a command.\n\n")
    if command == "upload":
        Imgur().post_album()
    elif command == "albums":
        Imgur().get_albums()
    elif command == "exit":
        Files.exit = True
    else:
        Files.displayError("Not a valid command.")


if __name__ == '__main__':
    startup()
    while Files.exit == False:
        listener()
    input("")
