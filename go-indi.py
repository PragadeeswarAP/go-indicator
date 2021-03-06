#!/usr/bin/env python
import sys
import pygtk
from gi.repository import Gtk, GLib, Gio, Gdk 
from gi.repository import AppIndicator3
import pycurl
from StringIO import StringIO
import xml.etree.ElementTree as ET
import webbrowser
import os.path

selectedPipelines = []
pathToIcon = "/media/yooo/5A3426C44A1D9AD2/Indix/Hackn8/MyGoPanel/go.png"
# urlOfXml = "http://abyss:8153/go/cctray.xml"
# pathToIcon = "/home/kumaran/Indix/go-indicator/go-logo.jpg"
# urlOfXml = "http://sivakumaran-hp:8153/go/cctray.xml"
# username = ''
# password = ''

class Job:

    name = ""
    lastBuildStatus = ""
    activity = ""
    url = ""

    def __init__(self, name, lastBuildStatus, activity, url):
        self.name = name
        self.lastBuildStatus = lastBuildStatus
        self.activity = activity
        self.url = url

class goIndicator:

    def __init__(self):
        self.ind = AppIndicator3.Indicator.new('go-indicator', '', AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.ind.set_icon(pathToIcon)
        self.ind.set_attention_icon("new-messages-red")      #change the icon
        if os.path.isfile("selectedPipelines.txt"):
            self.getSelectedPipelinesFromFile()

    def getXmlResponse(self, username, password, urlOfXml):
        try:
            responseBuffer = StringIO()
            curl = pycurl.Curl()
            curl.setopt(curl.URL, urlOfXml)
            curl.setopt(curl.WRITEFUNCTION, responseBuffer.write)
            curl.perform()
            curl.close()
            return responseBuffer.getvalue()
        except:
            print "Error in getting the xml response"

    def getSelectedPipelinesFromFile(self):
       try:
           with open("selectedPipelines.txt") as f:
               content = f.readlines()
           content = [x.strip('\n') for x in content]
           for pipeline in content:
            selectedPipelines.append(pipeline)
       except:
           print "Error while reading selectedPipelines from file"

    def loginUser(self):
       try:
           with open("test.txt") as f:
               content = f.readlines()
           content = [x.strip('\n') for x in content]
           print "content", content
           username = content[0]
           password = content[1]
           urlOfXml = content[2]
           return urlOfXml
       except:
           print "Error while reading user login details from file"
           return "Failure"


    def main(self):
       if os.path.isfile("test.txt"):   
           urlOfXml = self.loginUser()
           print selectedPipelines
           print "url", urlOfXml
           xml = self.getXmlResponse('', '', urlOfXml)
           [projectDetails, projectNameList] = self.parseXml(xml)
           self.createMenu(projectDetails, projectNameList)
           Gtk.main()
           #default refresh
           GLib.timeout_add_seconds(10, True)
       else:
           self.getUserInfo()
           Gtk.main()

    def parseXml(self, xml):
        projectDetails = {}
        projectNameList = []
        try:
            strXml = ET.fromstring(xml)
            for project in strXml.getiterator('Project'):
                pipenameParts = str(project.attrib["name"]).split(" :: ")
                projectName = pipenameParts[0]
                projectNameList.append(projectName)
                if pipenameParts[0] in selectedPipelines and len(pipenameParts) == 3:
                    stageName = pipenameParts[1]
                    jobName = pipenameParts[2]
                    activity = project.attrib['activity']
                    lastBuildStatus = project.attrib['lastBuildStatus']
                    url = project.attrib['webUrl']
                    jobObject = Job(jobName, activity, lastBuildStatus, url)
                    try:
                        projectDetails[projectName][stageName].append(jobObject)
                    except:
                        try:
                            projectDetails[projectName][stageName] = [jobObject]
                        except:
                            projectDetails[projectName] = {stageName : [jobObject]}
            projectNameList = list(set(projectNameList))          
            return [projectDetails, projectNameList]
        except:
            print "Error while parsing the xml"
                
        
    def getStatusImageForProject(self, project):
        for stage in project.keys():
            for job in project[stage]:
                print job.lastBuildStatus , job.activity
                if 'Building' in job.lastBuildStatus:
                    return Gtk.Image.new_from_icon_name("gtk-dialog-question", Gtk.IconSize.MENU)
                elif 'Failure' in job.activity:
                    return Gtk.Image.new_from_icon_name("gtk-stop", Gtk.IconSize.MENU)
        return Gtk.Image.new_from_icon_name("gtk-ok", Gtk.IconSize.MENU)

    def getStatusImageForJob(self, job):
        print job.activity
        if job.lastBuildStatus == "Building":
            return [-1,Gtk.Image.new_from_icon_name("gtk-dialog-question", Gtk.IconSize.MENU)]
        elif job.activity == "Failure":
            return [0,Gtk.Image.new_from_icon_name("gtk-stop", Gtk.IconSize.MENU)]
        else:
            return [1,Gtk.Image.new_from_icon_name("gtk-ok", Gtk.IconSize.MENU)]

    
    def createMenu(self, projectDetails, projectNameList):
        self.pipelineMenu = Gtk.Menu()
        print "details ", projectNameList, selectedPipelines
        try:
            for project in selectedPipelines:
                self.pipelineItem = Gtk.ImageMenuItem.new_with_label(project)
                self.pipelineItem.set_always_show_image(True)
                self.stageMenu = Gtk.Menu()
                stagesInProject = projectDetails[project].keys()
                img = self.getStatusImageForProject(projectDetails[project])
                for stage in stagesInProject:
                    # img = self.getStatusImageForStage(projectDetails[project])
                    self.stageItem = Gtk.ImageMenuItem.new_with_label(stage)
                    self.stageItem.set_always_show_image(True)
                    self.jobMenu = Gtk.Menu()
                    stageImg = Gtk.Image.new_from_icon_name("gtk-ok", Gtk.IconSize.MENU)
                    for job in projectDetails[project][stage]:
                        [flag,jobImg] = self.getStatusImageForJob(job)
                        if flag == -1:
                            stageImg = Gtk.Image.new_from_icon_name("gtk-dialog-question", Gtk.IconSize.MENU)
                        elif flag == 0:
                            stageImg = Gtk.Image.new_from_icon_name("gtk-stop", Gtk.IconSize.MENU)

                        self.jobItem = Gtk.ImageMenuItem.new_with_label(job.name)
                        self.jobItem.set_always_show_image(True)
                        self.jobItem.connect("activate", self.openUrl, job.url)
                        self.jobItem.set_image(jobImg)
                        self.jobItem.show()
                        self.jobMenu.append(self.jobItem)             
                    self.jobMenu.show()
                    self.stageItem.set_submenu(self.jobMenu)
                    self.stageItem.set_image(stageImg)
                    self.stageItem.show()
                    self.stageMenu.append(self.stageItem)
                self.stageMenu.show() 
                self.pipelineItem.set_submenu(self.stageMenu)
                self.pipelineItem.set_image(img)
                self.pipelineItem.show()
                self.pipelineMenu.append(self.pipelineItem)
        except:
            print "Error while creating menu"
        self.pipelineMenu.show()
       
        self.preferenceItem = Gtk.ImageMenuItem.new_with_label("Preference")
        self.preferenceItem.set_always_show_image(True)
        img = Gtk.Image.new_from_icon_name("system-run", Gtk.IconSize.MENU)
        self.preferenceItem.connect("activate", self.preference, projectNameList)
        self.preferenceItem.set_image(img)
        self.preferenceItem.show()
        self.pipelineMenu.append(self.preferenceItem)

        self.refreshItem = Gtk.ImageMenuItem.new_with_label("Refresh")
        self.refreshItem.set_always_show_image(True)
        img = Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.MENU)
        self.refreshItem.set_image(img)
        self.refreshItem.connect("activate", self.refresh)
        self.refreshItem.show()
        self.pipelineMenu.append(self.refreshItem)
        
        self.quit_item = Gtk.ImageMenuItem.new_with_label("Quit")
        self.quit_item.set_always_show_image(True)
        img = Gtk.Image.new_from_icon_name("system-shutdown", Gtk.IconSize.MENU)
        self.quit_item.set_image(img)
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.pipelineMenu.append(self.quit_item)
        
        self.ind.set_menu(self.pipelineMenu)

    def quit(self, widget):
        sys.exit(0)

    def openUrl(self, widget, url):
        new = 2 # open in a new tab, if possible
        webbrowser.open(url, new = new)

    def refresh(self, widget):
        self.main()

    def getUserInfo(self):
        window = Gtk.Window()
        window.set_title("Enter login details:")
        window.set_border_width(120)
        vbox = Gtk.VBox(True, 2)
        window.add(vbox)
        vbox.show()
        window.show()
        usernameLabel = Gtk.Label("Username : ")
        usernameLabel.show()
        vbox.pack_start(usernameLabel, True, True, 2)
        usernameBox = Gtk.Entry()
        usernameBox.set_visibility(True)
        vbox.pack_start(usernameBox, True, True, 2)
        usernameBox.show()
        passwdLabel = Gtk.Label("Password : ")
        passwdLabel.show()
        vbox.pack_start(passwdLabel, True, True, 2)
        passwdBox = Gtk.Entry()
        passwdBox.set_visibility(False)
        vbox.pack_start(passwdBox, True, True, 2)
        passwdBox.show()
        urlLabel = Gtk.Label("Url : ")
        urlLabel.show()
        vbox.pack_start(urlLabel, True, True, 2)
        urlBox = Gtk.Entry()
        urlBox.set_visibility(True)
        vbox.pack_start(urlBox, True, True, 2)
        urlBox.show()
        button = Gtk.Button("Ok")
        button.connect("clicked", self.onButtonClick, window, usernameBox, passwdBox, urlBox)
        vbox.pack_start(button, True, True, 2)
        button.show()
        
    def onButtonClick(self, widget, window, usernameBox, passwdBox, urlBox):
        try:
            file = open("test.txt",'w')
            file.write(usernameBox.get_text() + '\n' + passwdBox.get_text() + '\n' + urlBox.get_text())
            file.close()
            window.close()
            self.main()

        except:
            print "Error while writing user login details to file"

    def writeSelectedPipelines(self):
        try:
            file = open("selectedPipelines.txt",'w+')
            for pipeline in selectedPipelines:
                file.write(pipeline + '\n')
            file.close()

        except:
            print "Error while writing selectedPipelines to file"


    def preference(self, widget, projectNameList):
        window = Gtk.Window()
        window.set_title("Select Pipelines")
        window.set_border_width(80)
        vbox = Gtk.VBox(True, 2)
        window.add(vbox)
        for project in projectNameList:
            button = Gtk.CheckButton(project)
            button.connect("toggled", self.updateSelectedPipelines, project)
            vbox.pack_start(button, True, True, 2)
            if project in selectedPipelines:
                button.set_active(project)
            button.show()
        window.show()
        button = Gtk.Button("Quit")
        button.connect("clicked", self.delete_event, window)
        vbox.pack_start(button, True, True, 2)
        button.show()
        vbox.show()
        


    def updateSelectedPipelines(self, button, name):
        if button.get_active() and name not in selectedPipelines:
            state = "on"
            selectedPipelines.append(name)
        elif not button.get_active() and name in selectedPipelines:
            state = "off"
            selectedPipelines.remove(name)

        print "selected Pipelines", selectedPipelines

    def delete_event(self, button, window):
        self.writeSelectedPipelines()
        window.close()
        self.main()

if __name__ == "__main__":
    indicator = goIndicator()
    indicator.main()