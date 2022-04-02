from asyncio.windows_events import NULL
from calendar import day_abbr
from optparse import Values
from platform import machine
import re
from django.http import HttpResponse
from django.shortcuts import redirect, render

#Libraries to authenticate the user and then login and logout and show error if authentication data is incorrect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

#Library to run commands on a machine
from subprocess import check_output
import paramiko
from paramiko import BadHostKeyException
from paramiko import AuthenticationException
from paramiko import SSHException

from .models import sshData
from .forms import CreateUser
from . import sshConnect, models

# Create your views here.
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('index')

    elif request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Username or Password is incorrect!')
            return redirect('login')
    else:
        return render(request, 'login.html',)

def signupPage(request):
    if request.method=='POST':
        form = CreateUser(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account Created Successfully.")
            return redirect('login')
        else:
            messages.error(request, "There was a problem creating account.")
            return redirect('signup')
    else:
        form = CreateUser()
        values = {'form': form}
        return render(request, 'signup.html', values)

def serverData(request):
    return render(request, 'serverdata.html',)

def index(request):
    if request.user.is_authenticated:
        user = request.user
        values = {"user": user}
        return render(request, 'index.html', values)
    else:
        return HttpResponse("<h1>Please log in to continue.<h1>")

def backup(request):
    logout(request)
    return redirect('login')
    #return render(request, "backup.html", )

def process(request):
    if request.user.is_authenticated:
        user = request.user

        #Command to retireve the running processes
        process_command = 'top -b | head -n 30'

        #List to store the data from the top command
        process_list = []

        #Executing command to get the result
        result = sshConnect.connect(process_command, user)
        if len(result)!=0:
            for val in result:
                process_list.append(val.split("\n"))
        
        #Creating a dictionary to pass list values to template
        values = {"processData": process_list}

        return render(request, 'monitorprocess.html', values)
    else:
        return HttpResponse("<h1>Please log in to continue.<h1>")

def users(request):
    if request.user.is_authenticated:
        user = request.user
        #To get the data of the logged in users

        #Commands for login and failed login data
        login_command = 'who'
        badLogin_command = 'cat /var/log/auth.log | grep "Failed password"'

        #Lists to store information retrieved from commands
        lst1 = []   #list 1 stores the message part for failed login
        lst2 = []   #list 2 stores the actual data part for failed login
        login = []  #intermediate list to capture and divide data
        badLogin = []
        values = {}
        badLogin_dict = {}

        #Executing both commands and storing data in respective lists
        result = sshConnect.connect(login_command, user)
        if len(result)!=0:
            for val in result:
                login.append(val.split())

        result = sshConnect.connect(badLogin_command, user)
        if len(result)!=0:
            for val in result:
                badLogin.append(val.split(": "))

        """ for val in badLogin[0::2]:
            lst2.append(val.strip(" "))
        
        lst1.clear()
        for val in badLogin[1::2]:
            lst1.append(val) """

        #badLogin_dict = dict(zip(lst2, lst1))

        #Passing the list data to dictionary
        values = {"login": login, "badLogin": badLogin}
        return render(request, 'users.html', values)

    else:
        return HttpResponse("<h1>Please log in to continue.<h1>")

def diskSpace(request):
    if request.user.is_authenticated:
        user = request.user

        #Commands for the three parts of the interfaces
        command_disk = "df -h | sed '1d'"
        command_devsda = "df -h | grep 'dev/sda'"
        command_devsdb = "df -h | grep 'dev/sdb'"

        #List to store the data that is passed to the three interfaces
        lst1 = []
        disk_data = []
        devsda_data = []
        devsdb_data = []

        #Three commands are executed and data is store in the respective list 
        result = sshConnect.connect(command_disk, user)
        if len(result)!=0:
            for val in result:
                lst1.append(val.split("\n"))

        for data in lst1:
            for val in data:
                disk_data.append(val.split())

        lst1.clear()
        result = sshConnect.connect(command_devsda, user)
        if len(result)!=0:
            for val in result:
                lst1.append(val.split("\n"))
        
        for data in lst1:
            for val in data:
                devsda_data.append(val.split())

        lst1.clear()
        result = sshConnect.connect(command_devsdb, user)
        if len(result)!=0:
            for val in result:
                lst1.append(val.split("\n"))
        
        for data in lst1:
            for val in data:
                devsdb_data.append(val.split())

        devsda_data = devsda_data + devsdb_data

        #Data is passed as dictionary to the template
        values = {"diskData": disk_data, "devsdaData": devsda_data}
        return render(request, 'diskspace.html', values)
    else:
        return HttpResponse("<h1>Please log in to continue.<h1>")

def cmdOutput(request):
    return render(request, 'cmdoutput.html', )