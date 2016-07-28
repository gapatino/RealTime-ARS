# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 10:25:59 2016

@author: patino


REAL TIME MONITORING OF AUDIENCE RESPONSE SYSTEM  
TKinter version  
Gustavo A. Patino and Sarah Lerchenfeldt  
July, 2016

The script allows management of audience responses in real time by displaying 
which user picked which answer  
It was designed to be used with iClickers. The user needs access to two 
files to display results of polling sessions:  
1. A CSV file containing the name of the audience members in one column and 
   the id number of their iClicker in another column. Each row is composed of
   audience member name and iClicker id separated by a comma. The script also 
   provides the interface to create and modify the CSV file  
2. The XML file in which the iClicker base is saving the responses for the 
   current polling session. Each session is composed of multiple questions. 
   This script will display the answers for the latest question  in the 
   current polling session
"""

import csv
import os
import xml.etree.cElementTree as etree
import tkinter
from tkinter import *
from tkinter import ttk  
from tkinter import messagebox
from tkinter import filedialog


def dispResults1():
    ''' invoke function to call the csv and xml files, if they return false
    then return to main menu. Otherwise should return three objects: One is
    the name of the XML file, second is a dictionary of students and their 
    iClicker ID, the other a list of lists with first sublist iClicker ID
    and second sublist their answer choice for the latest question in the 
    polling session. 
    Pass the dictionary and list of lists to organizedResults, which returns 
    two objects: First, a dictionary of student ID as key and as value a list
    of all the answer choices that student has picked in chronological order.
    Second, a lost of lists with six sublists: the iClicker ID of those that 
    chose options A-E, and those that did not make any choice.
    The list of lists is then passed to resultWindow which displays the answers
    in the screen.
    Upon closing the first display call dispResults2 that will do the cycling
    through all the polling questions'''
    gotfiles=getFiles()
    if (gotfiles==False):
        return
    # extract the different information objects from gotfiles, if there is
    # an error show a warning and go back to main menu
    try:
        sessionfile=gotfiles[0]
        iclickerdict=gotfiles[1]
        pollanswers=gotfiles[2]
        studentlist=gotfiles[3]
    except:
        m3=messagebox.showinfo(message='There was a problem with the files\
                \nPlease try again')
        return
    # call organizedResults to get back a list of which students pick each 
    # answer choice
    try:
        cumresults, organizedresults=organizedResults(iclickerdict,pollanswers)
    except:
        m3=messagebox.showinfo(message='Incompatible information in the files\
                \nPlease try again')
        return
    # get timestamp of sessionfile for tracking that it changes later, 
    # then call resultWindow to show poll results
    sessionfiletime=os.path.getmtime(sessionfile)
    resultWindow(organizedresults)
    # from here on need a while loop to cycle through each poll
    counter=0
    while (counter==0):
        m4=messagebox.askquestion(message='Do you want to display the results\
         \nof another poll?')
        if (m4=='no'):
            counter=1
        else:
            m5=messagebox.showinfo(message='Run a new poll and press OK to \
            display new results')
            # Check that sessionfile has been updated since last read
            if (sessionfiletime==os.path.getmtime(sessionfile)):
                m6=messagebox.showinfo(message='No new polls in the XML file\
                \nsince last read \n Please close the new poll')
            else:
                sessionfiletime=os.path.getmtime(sessionfile)
            # Get the new pollanswers
            pollanswers=getPollResults(sessionfile)
            # Run organizedResults again
            cumresults1, organizedresults=organizedResults(iclickerdict,
                                                          pollanswers)
            # Add results from cumresults1 to cumresults
            for index in cumresults1.keys():
                cumresults[index].append(cumresults1[index])
            # Display new results
            resultWindow(organizedresults)
    # When all polls are finished offer to save the results
    m4=messagebox.askquestion(message='Do you want to save the results\
         \nof the polling session?')
    if (m4=='no'):
        return
    else:
        savesession = saveSession(cumresults, studentlist)        
        return


def saveSession(cumresults, studentlist):
    ''' First function of two to save the polling results in a .csv file
    This one gets the name of the file where results will be saved
    Then passes cumresults and studentlist to makeSessionCsv to do the 
    actual saving. If the latter function returns an error triggers a warning'''
    # Determine number of questions
    counter=0
    while counter==0:
        namecsvfile=filedialog.asksaveasfilename(defaultextension=".csv") 
        if namecsvfile=='':
            m2=messagebox.askquestion(message='No file was selected \
            \nDo you want to try again?')
            if m2=='no': 
                counter=1
        else:
            try:
                makeSessionCsv(namecsvfile, cumresults, studentlist)                
                counter=1
            except:
                m3=messagebox.showinfo(message='There was a problem with the file\
                \nPlease try again')    
    return


def makeSessionCsv(namecsvfile, cumresults, studentlist):
    ''' Called from saveSession, receives namecsvfile (name of the file in 
    which session results will be saved), cumresults (dictionary of students ID
    as key and answer choices for each question as value), and studentlist 
    (list of student IDs in the same order as in the original file matching 
    them to iClicker IDs). Saves a .csv file with name namecsvfile whose 
    headers are Student/Team and then each question number. Subsequent rows
    are the student ID (in same order as in original csv file) and the answer
    choice for each question'''
    # Get number of questions
    nquestions=len(cumresults[studentlist[0]])    
    with open(namecsvfile, 'w') as outcsv:
        writer=csv.writer(outcsv, delimiter=',', quotechar='|', 
                          quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        # Add column headers
        header=['Student/Team']
        for i in range(nquestions):
            index='Question ' + str(i+1)
            header.append(index)
        writer.writerow(header)
        # Add each student ID row
        for studentid in studentlist:
            row=[studentid] # first column is studentID
            rowanswers=cumresults[studentid] # Extract list of answers for ID
            for i in rowanswers:
                row.extend(i)
            writer.writerow(row)
    # Display confirmatory message
    m4=messagebox.showinfo(message='File saved')
    return


def organizedResults(iclickerdict, pollanswers):
    ''' Takes iclickerdict and pollanswers and will return two objects: 
    First, a dictionary of student ID as key and as value a list
    of all the answer choices that student has picked in chronological order.
    Second, a lost of lists with six sublists: the iClicker ID of those that 
    chose options A-E, and those that did not make any choice '''
    # Initialize variables for the dictionary and sublists
    cumresults={}
    choicea=[]
    choiceb=[]
    choicec=[]
    choiced=[]
    choicee=[]
    choiceno=[]
    for index, _ in enumerate(pollanswers[1]):
        # Populate the dictionary 
        cumresults.update({iclickerdict[pollanswers[0][index]]:
            [pollanswers[1][index]]})
        # Populate the sublists
        if (pollanswers[1][index]=="A"):
            choicea.append(iclickerdict[pollanswers[0][index]])
        elif (pollanswers[1][index]=="B"):
            choiceb.append(iclickerdict[pollanswers[0][index]])
        elif (pollanswers[1][index]=="C"):
            choicec.append(iclickerdict[pollanswers[0][index]])
        elif (pollanswers[1][index]=="D"):
            choiced.append(iclickerdict[pollanswers[0][index]])
        elif (pollanswers[1][index]=="E"):
            choicee.append(iclickerdict[pollanswers[0][index]])
        else:
            choiceno.append(iclickerdict[pollanswers[0][index]])
    # If a student ID did not submit answer there won't be info in XML file
    # check that all keys in iclickerdict are present in cumresults and if 
    # not adjust cumresults and choice sublists
    for index in iclickerdict.keys():
        if not(iclickerdict[index] in cumresults):
            cumresults.update({iclickerdict[index]:""})
            choiceno.append(iclickerdict[index])
    # Create the list of lists from the sublists
    organizedresults=[choicea, choiceb, choicec, choiced, choicee, choiceno]
    return cumresults, organizedresults
        
        
def resultWindow(organizedresults):
    ''' Displays polling results in a Toplevel window '''
    resultwindow=Toplevel(root, bg="gray93", padx=10, pady=10)
    resultwindow.title('Polling results')

    # Column headers
    headera=ttk.Label(resultwindow, text='Choice A', anchor='center', 
            font=("Helvetica", 16), padding=5, width=17)
    headera.grid(column=0, row=0)
    headerb=ttk.Label(resultwindow, text='Choice B', anchor='center', 
            font=("Helvetica", 16), padding=5, width=17)
    headerb.grid(column=1, row=0)
    headerc=ttk.Label(resultwindow, text='Choice C', anchor='center', 
             font=("Helvetica", 16), padding=5, width=17)
    headerc.grid(column=2, row=0)
    headerd=ttk.Label(resultwindow, text='Choice D', anchor='center', 
             font=("Helvetica", 16), padding=5, width=17)
    headerd.grid(column=3, row=0)
    headere=ttk.Label(resultwindow, text='Choice E', anchor='center', 
             font=("Helvetica", 16), padding=5, width=17)
    headere.grid(column=4, row=0)
    headerno=ttk.Label(resultwindow, text='No Choice', anchor='center', 
             font=("Helvetica", 16), padding=5, width=17)
    headerno.grid(column=5, row=0)
   
    #Determine length of longest sublist to use as height of listboxes
    maxlength=max([len(organizedresults[0]), len(organizedresults[1]), 
                  len(organizedresults[2]), len(organizedresults[3]),
                  len(organizedresults[4]), len(organizedresults[5]) ])    
   
    # Results as listboxes
    resultsa=Listbox(resultwindow, height=maxlength, bg="white")
    for item in organizedresults[0]:
        resultsa.insert(END, "  "+item)
    resultsa.grid(column=0, row=1)
    resultsb=Listbox(resultwindow, height=maxlength,  bg="white")
    for item in organizedresults[1]:
        resultsb.insert(END, "  "+item)
    resultsb.grid(column=1, row=1)
    resultsc=Listbox(resultwindow, height=maxlength,  bg="white")
    for item in organizedresults[2]:
        resultsc.insert(END, "  "+item)
    resultsc.grid(column=2, row=1)
    resultsd=Listbox(resultwindow, height=maxlength,  bg="white")
    for item in organizedresults[3]:
        resultsd.insert(END, "  "+item)
    resultsd.grid(column=3, row=1)
    resultse=Listbox(resultwindow, height=maxlength,  bg="white")
    for item in organizedresults[4]:
        resultse.insert(END, "  "+item)
    resultse.grid(column=4, row=1)
    resultsno=Listbox(resultwindow, height=maxlength,  bg="white")
    for item in organizedresults[5]:
        resultsno.insert(END, "  "+item)
    resultsno.grid(column=5, row=1)
    # Add button to close the window
    closebutton1=ttk.Button(resultwindow, text='Close', 
                            command=resultwindow.destroy)
    closebutton1.grid(row=2)
    root.wait_window(resultwindow)

    
def getFiles():
    ''' Gets names of csv and xml files and makes sure the data can be retrieved
    in a useful manner '''
    # Get the file with the iClicker information  
    m1=messagebox.showinfo(message='Select CSV file with the iClicker \
    information')  
    counter=0
    while counter==0:
        iclickerfile=filedialog.askopenfilename() #notice all lowercase 
        if iclickerfile=='':
            m2=messagebox.askquestion(message='No file was selected \
            \nDo you want to try again?')
            if m2=='no': return False #if no then go back to main menu
        else:
            # If got a filename extract the data            
            try:
                studentlist, iclickerdict=getiClickerData(iclickerfile)
                counter=1
            except:
                m3=messagebox.showinfo(message='There was a problem with the file\
                \nPlease try again')
    
    # Get the XML file from current session
    m1=messagebox.showinfo(message='Select XML file from current iClicker \
    session')  
    counter=0
    while counter==0:
        sessionfile=filedialog.askopenfilename() #notice all lowercase 
        if sessionfile=='':
            m2=messagebox.askquestion(message='No file was selected \
            \nDo you want to try again?')
            if m2=='no': return False #if no then go back to main menu
        else:
            # If got a filename extract the data            
            print(sessionfile, ' selected')            
            try:
                pollanswers=getPollResults(sessionfile)
                counter=1
            except:
                m3=messagebox.showinfo(message='There was a problem with the file\
                \nPlease try again')
    
    # return both iclickerdict and pollanswers to function dispResults
    return [sessionfile, iclickerdict, pollanswers, studentlist]
 
               
def getPollResults(sessionfile):
    ''' Receives name of xml file and returns paired lists of students ID and
    answer choice '''    
    tree=etree.parse(sessionfile)
    xmlroot=tree.getroot() 
    if len(xmlroot[0].findall('v'))==0:
        return #Might not be iclicker file, go back to getFiles, trigger error
    # declare variables to store students ID and answer choice
    studentid=[]
    answerchoice=[]
    # find what attribute of the root corresponds to the last <p>...</p> 
    # question block
    lastq=len(xmlroot)-1
    # Iterate through each of the iClicker answers submitted in a question
    for child in xmlroot[lastq].findall('v'):
        # For each answer extract student ID and choice made and append them to
        # storing variables
        studentid.append(child.attrib['id'])
        answerchoice.append(child.attrib['ans'])
    # Make a new variable storing both lists and return the new variable
    pollanswers=[studentid,answerchoice]
    return pollanswers

            
def getiClickerData(iclickerfile):
    ''' Receives name of csv file and returns a dictionary of iClickerID (keys)
    and student ID (values) and a list of student ID in same order as in the
    original file. The latter to be used when saving session results'''
    dict1={}
    list1=[]
    with open(iclickerfile, newline='') as csvfile:
        document=csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in document:
            list1.append(row[0])
            dict1.update({row[1]:row[0]})
            # Notice how iClicker ID is key and student ID is value
        return list1, dict1
    

def editiClickerInfo():
    ''' Is called by edit_info_button. Displays a Toplevel window with two 
    buttons: One to create a new iClicker information file, the other to
    edit an existing file. Each button has a function bound that destroys this
    current Toplevel window and then executes the desired choice'''
    createoredit=Toplevel(root, bg="gray93", padx=10, pady=10)  
    createoredit.title('Edit iClicker information')
    createiclickerfile=ttk.Button(createoredit, text='Create new iClicker file', 
                            command=createiClickerFile)    
    createiclickerfile.grid(row=0)
    editiclickerfile=ttk.Button(createoredit, text='Edit existing iClicker file', 
                            command=editiClickerFile)    
    editiclickerfile.grid(row=1)
    # To control when this window gets closed will use the value of a TKinter
    # boolean variable
    global close_this_window
    close_this_window=BooleanVar(value=False)
    print('close_this_window value: ',close_this_window.get())
    if (close_this_window==True): 
        createoredit.destroy()
    root.wait_window(createoredit)
    return


def createiClickerFile():
    ''' Called from editiClickerInfo. Sets the values for the variables
    iclickerdict (dictionary of iClickerID (keys) and student ID (values)),
    iclickerfile (csv file where the info for iclicker dict was stored as
    second and first column respectively - yes the order in the csv file is
    inverted with respect to the iclickerdict variable), and studentlist (list
    of student IDs in the same order as user enters them, needed in addition to
    iclickerdict because dictionaries are not ordered) as empty and passes 
    those values to iClickerManager, a common interface for both 
    createiClickerFile and editiClickerFile'''
    # First change the value of close_this_window so the createoredit Toplevel
    # is destroyed
    close_this_window.set(True)    
    # Initialize the empty variables
    iclickerdict={}
    iclickerfile=""
    studentlist=[]
    print('createiClickerFile')
    print('close_this_window value: ',close_this_window.get())
    return
    
    
def editiClickerFile():
    ''' Called from editiClickerInfo. Sets the values for the variables
    iclickerdict (dictionary of iClickerID (keys) and student ID (values)),
    iclickerfile (csv file where the info for iclicker dict was stored as
    second and first column respectively - yes the order in the csv file is
    inverted with respect to the iclickerdict variable), and studentlist (list
    of student IDs in the same order as user enters them, needed in addition to
    iclickerdict because dictionaries are not ordered) using the filebrowser
    and getiClickerData function. It then passes those values to 
    iClickerManager, a common interface for both createiClickerFile and 
    editiClickerFile'''
    # Initialize the variables
    # Get the file with the iClicker information  
    m1=messagebox.showinfo(message='Select CSV file with the iClicker \
    information')  
    counter=0
    while counter==0:
        iclickerfile=filedialog.askopenfilename() #notice all lowercase 
        if iclickerfile=='':
            m2=messagebox.askquestion(message='No file was selected \
            \nDo you want to try again?')
            if m2=='no': return #if no then go back to main menu
        else:
            # If got a filename extract the data            
            try:
                studentlist, iclickerdict=getiClickerData(iclickerfile)
                counter=1
            except:
                m3=messagebox.showinfo(message='There was a problem with the file\
                \nPlease try again')
    print('editiClickerFile')            
    
    
    return
    

def exitFunction():
    ''' Close program '''
    root.destroy()
    #quit()


# Create the root window
root=Tk()
root.title("RealTime ARS")

# Create a frame that will contain the main menu
mf_mainmenu=ttk.Frame(root, padding='12 12 12 12')
mf_mainmenu.grid(column=0, row=0, sticky=(N, W, E, S))
mf_mainmenu.columnconfigure(0,weight=1)
mf_mainmenu.rowconfigure(0, weight= 1)

# Add title element
title1=ttk.Label(mf_mainmenu, text='RealTime ARS', anchor='center', 
                 font=("Helvetica", 16))
title1.grid(column=2, row=0)

# Add buttons
disp_result_button=ttk.Button(mf_mainmenu, text='Display Session Results',
                              command=dispResults1)
disp_result_button.grid(column=2, row=1, sticky=(W, E))

edit_info_button=ttk.Button(mf_mainmenu, text='Edit iClicker information', 
                            command=editiClickerInfo)
edit_info_button.grid(column=2, row=2, sticky=(W, E))

exit_button=ttk.Button(mf_mainmenu, text='Exit', command=exitFunction)
exit_button.grid(column=2, row=3, sticky=(W, E))

# Add footer
title2=ttk.Label(mf_mainmenu, text='Version 1.0, 2016', anchor='center')
title2.grid(column=2, row=4)
                 
for child in mf_mainmenu.winfo_children():
    child.grid_configure(padx=5, pady=5)
        
root.mainloop()