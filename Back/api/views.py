from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.db.models import Q

from .models import User, Project
from hobbyshare import settings

import datetime
import json
import re
import smtplib
import base64
import os

def set_cookie(response, key, value, days_expire = 7):
  if days_expire is None:
    max_age = 365 * 24 * 60 * 60  #one year
  else:
    max_age = days_expire * 24 * 60 * 60 
  expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
  response.set_cookie(key,
                      value,
                      max_age=max_age,
                      expires=expires,
                      domain=settings.SESSION_COOKIE_DOMAIN,
                      #secure=settings.SESSION_COOKIE_SECURE or None,
                      #httponly=True,
                      #samesite='None'
                      )

@csrf_exempt
@require_GET
def check_login(request):
    response = HttpResponse()
    
    #   Check if sessionid is present
    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '':
        response.write("False")
        return response

    if User.objects.filter(sessionid = request.COOKIES.get('sessionid'), verified = True).count() is 1:
        response.write("True")
    else:
        response.write("False")
    return response

@csrf_exempt
@require_POST
def check_username(request):
    response = HttpResponse()

    if 'username' not in request.POST or request.POST['username'] is '':
        response.write("False")
        return response

    if User.objects.filter(username=request.POST['username']).count() > 0:
        response.write("False")
    else:
        response.write("True")

    return response

@csrf_exempt
@require_POST
def check_email(request):
    response = HttpResponse()

    if 'email' not in request.POST or request.POST['email'] is '':
        response.write("Bad Email")
        return response

    email = re.search(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", request.POST['email'], flags=re.I).group()
    if email is None:
        response.write("Bad Email")
        return response

    if User.objects.filter(email=request.POST['email']).count() > 0:
        response.write("False")
    else:
        response.write("True")

    return response

@csrf_exempt
@require_POST
def sign_up(request):
    #   Create HTTP response
    response = HttpResponse()

    #   Check if all required fields are filled
    #   If any are missing, return array of missing fields
    if 'password' not in request.POST or request.POST['password'] is '' or \
    'fname' not in request.POST or request.POST['fname'] is '' or \
    'lname' not in request.POST or request.POST['lname'] is '' or \
    'username' not in request.POST or request.POST['username'] is '' or \
    'email' not in request.POST or request.POST['email'] is '':
        missing = []
        if 'fname' not in request.POST or request.POST['fname'] is '':
            missing.append("fname")
        if 'lname' not in request.POST or request.POST['lname'] is '':
            missing.append("lname")
        if 'username' not in request.POST or request.POST['username'] is '':
            missing.append("username")
        if 'password' not in request.POST or request.POST['password'] is '':
            missing.append("password")
        if 'email' not in request.POST or request.POST['email'] is '':
            missing.append("email")
        response.write(json.dumps(missing))
        return response

    #   Check if username is in use already
    if User.objects.filter(username = request.POST['username']).count() > 0:
        response.write("Duplicate Username")
        return response

    #   Check if password meets minimum length
    if len(request.POST['password']) < 12:
        response.write("Password Short")
        return response

    #   Check if email address is in correct format
    email = re.search(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", request.POST['email'], flags=re.I)
    if email is None or email.group() is not request.POST['email']:
        response.write("Bad Email")
        return response

    #   Check if email is in use already
    if User.objects.filter(email = request.POST['email']).count() > 0:
        response.write("Duplicate Email")
        return response

    #   Hash and salt password
    password = make_password(request.POST['password'])

    #   Generate authentication token
    token = get_random_string(length=32)

    #   Extract optional image
    optionalPic = request.FILES['profilepic'] if 'profilepic' in request.FILES else None

    #   Reject request if included picture is larger than 10 MB
    if optionalPic is not None and optionalPic.size > 1048576:
        response.write("File Too Big")
        return response

    #   Compose email message
    message = 'Your HobbyShare.app Verification Token:\n\n%s\n\n' % token
    message += 'To verify your HobbyShare.app account:\n'
    message += '1. Copy the above token.\n'
    message += f'2. Paste the token into the verification page: https://{os.getenv("DJANGO_HOST")}/verify/user/\n'
    message += '3. Click the verify button. You will receive a confirmation email when your account has been verified.\n'

    #   Send verification email to user
    try:
        send_mail(
            'HobbyShare.app Verification',
            message,
            f'no-reply@{os.getenv("DJANGO_HOST")}',
            [request.POST['email']],
            fail_silently = False,
        )
    except (smtplib.SMTPException, smtplib.SMTPRecipientsRefused) as e:
        response.write("Bad Email")
        return response

    #   Create user in database
    user = User.objects.create(
        fname = request.POST['fname'],
        lname = request.POST['lname'],
        username = request.POST['username'],
        password = password,
        email = request.POST['email'],
        skills = request.POST['skills'],
        profilepic = optionalPic,
        token = token,
        contributing = json.dumps([])
        )

    response.write('True')

    return response

@csrf_exempt
@require_POST
def verify_user(request):
    #   Create HTTP response
    response = HttpResponse()

    #   Check if token is present and valid
    if 'token' not in request.POST or request.POST['token'] is '':
        response.write("False")
        return response

    user = User.objects.filter(token = request.POST['token'], verified = False)
    if user.count() is not 1:
        response.write("False")
        return response

    #   Update verified boolean and remove token from user
    user = user.get()
    user.verified = True
    user.token = None;
    user.save()

    #   Check for duplicate users and remove
    duplicates = User.objects.filter(username = user.username, verified = False)
    duplicates.delete()

    response.write("True")
    return response

@csrf_exempt
@require_POST
def log_in(request):
    #   Create HTTP response
    response = HttpResponse()

    #   Check if all required fields are filled
    #   Check if username is valid
    #   If any are missing, return empty cookie
    if 'username' not in request.POST or request.POST['username'] is '' or \
    'password' not in request.POST or request.POST['password'] is '' or \
    User.objects.filter(username = request.POST['username'], verified = True).count() is not 1:
        response.write("False")
        return response

    #   Check password
    #   If not valid, return bad login
    user = User.objects.filter(username = request.POST['username'], verified = True).get()
    if check_password(request.POST['password'], user.password) is False:
        response.write("False")
        return response

    #   Create sessionid
    sessionid = get_random_string(length=128)

    #   Store sessionid in database
    user.sessionid = sessionid
    user.save()

    response.write("True")

    #   Store sessionid in cookie
    set_cookie(response, 'sessionid', sessionid)
    return response

@csrf_exempt
@require_POST
def log_out(request):
    response = HttpResponse()

    #   Check if sessionid is present
    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '':
        return response

    #   Find user with given sessionid
    user = User.objects.get(sessionid=request.COOKIES.get('sessionid'))
    #   Remove sessionid from database
    user.sessionid = None
    user.save()

    #   Remove sessionid from cookie
    set_cookie(response, 'sessionid', '')

    return response

@csrf_exempt
@require_POST
def email(request):
    response = HttpResponse()

    #   Check if all required fields are filled
    #   If any are missing, return array of missing fields
    if 'from' not in request.POST or request.POST['from'] is '' or \
    'message' not in request.POST or request.POST['message'] is '' or \
    'subject' not in request.POST or request.POST['subject'] is '':
        missing = []
        if 'subject' not in request.POST or request.POST['subject'] is '':
            missing.append("subject")
        if 'from' not in request.POST or request.POST['from'] is '':
            missing.append("from")
        if 'message' not in request.POST or request.POST['message'] is '':
            missing.append("message")
        response.write(json.dumps(missing))
        return response

    #   Check if email address is in correct format
    email = re.search(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", request.POST['from'], flags=re.I)
    if email is None or email.group() is not request.POST['from']:
        response.write("Bad Email")
        return response

    contactEmail = os.getenv("DJANGO_CONTACT_EMAIL")

    #   Attempt to send email to our contact email address
    try:
        send_mail(request.POST['subject'],
                  request.POST['message'],
                  request.POST['from'],
                  [contactEmail],
                  fail_silently = False)
    except (smtplib.SMTPException, smtplib.SMTPRecipientsRefused) as e:
        response.write("False")
        return response

    response.write("True")
    return response

@csrf_exempt
@require_POST
def forgot_user(request):
    response = HttpResponse()
    response.write("True")

    if 'email' not in request.POST or request.POST['email'] is '':
        return response

    user = User.objects.filter(email = request.POST['email'])
    if user.count() is not 1:
        return response

    user = user.get()
    message = 'Your HobbyShare.app Username:\n\n%s\n\n' % user.username

    try:
        send_mail(
            'HobbyShare.app Username',
            message,
            'no-reply@hobbyshare.app',
            [user.email],
            fail_silently = False,
        )
    except (smtplib.SMTPException, smtplib.SMTPRecipientsRefused) as e:
        return response

    return response

@csrf_exempt
@require_POST
def forgot_password(request):
    response = HttpResponse()
    response.write("True")

    if 'username' not in request.POST or request.POST['username'] is '':
        return response

    user = User.objects.filter(username = request.POST['username'])
    if user.count() is not 1:
        return response

    #   Generate authentication token
    token = get_random_string(length=32)
    user = user.get()
    user.token = token
    user.save()

    message = 'Your HobbyShare.app Password Reset Token:\n\n%s\n\n' % token
    message += 'To reset your password:\n'
    message += '1. Copy the above token.\n'
    message += '2. Paste the token into the password reset page: https://hobbyshare.app/reset/password/\n'
    message += '3. Enter your new password and confirm it. Passwords must be a minimum of 12 characters long.\n'
    message += '4. Click the reset button. You will receive a confirmation email when your password has been reset.\n'

    try:
        send_mail(
            'HobbyShare.app Password Reset',
            message,
            'no-reply@hobbyshare.app',
            [user.email],
            fail_silently = False,
        )
    except (smtplib.SMTPException, smtplib.SMTPRecipientsRefused) as e:
        return response

    return response

@csrf_exempt
@require_POST
def reset_password(request):
    response = HttpResponse()
    
    if 'token' not in request.POST or request.POST['token'] is '' or \
    'password' not in request.POST or request.POST['password'] is '':
        missing = []
        if 'token' not in request.POST or request.POST['token'] is '':
            missing.append("token")
        if 'password' not in request.POST or request.POST['password'] is '':
            missing.append("password")
        response.write(json.dumps(missing))
        return response

    user = User.objects.filter(token = request.POST['token'])
    if user.count() is not 1:
        response.write("False")
        return response

    if len(request.POST['password']) < 12:
        response.write('Password Short')
        return response

    password = make_password(request.POST['password'])

    user = user.get()
    user.verified = True
    user.token = None
    user.password = password
    user.save()

    message = 'Your HobbyShare.app account password has been successfully reset.'

    try:
        send_mail(
            'New HobbyShare.app Password',
            message,
            'no-reply@hobbyshare.app',
            [user.email],
            fail_silently = False,
        )
    except (smtplib.SMTPException, smtplib.SMTPRecipientsRefused) as e:
        response.write("Fail")
        return response

    response.write("True")
    return response


@require_GET
def fetch_username(request):
    response = HttpResponse()
    
    #   Check if sessionid is present
    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '':
        response.write("False")
        return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))

    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    response.write(user.username)
    return response

@require_GET
def get_user(request, username):
    response = HttpResponse()
    message = {}

    user = User.objects.filter(username = username)
    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    if bool(user.profilepic) is True:
        with open(user.profilepic.path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            message["profilepic"] = image_data

    message["fname"] = user.fname
    message["lname"] = user.lname
    message["username"] = user.username
    message["skills"] = user.skills
    message["projects"] = user.projects
    message["contributing"] = user.contributing

    if 'sessionid' in request.COOKIES and request.COOKIES.get('sessionid') is not '' and \
        User.objects.filter(sessionid = request.COOKIES.get('sessionid'), verified = True).count() is 1:
        message["email"]=user.email

        if User.objects.filter(sessionid = request.COOKIES.get('sessionid'),
                               verified = True,
                               username = username).count() is 1:
            message["match"] = "True"
        else:
            message["match"] = "False"
    else:
        message["match"] = "False"

    response.write(json.dumps(message))
    return response

@require_GET
def get_self(request):
    response = HttpResponse()

    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '' :
       response.write("No Session")
       return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))

    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    message = {}

    if bool(user.profilepic) is True:
        with open(user.profilepic.path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            message["profilepic"] = image_data

    message["fname"] = user.fname
    message["lname"] = user.lname
    message["username"] = user.username
    message["email"] = user.email
    message["skills"] = user.skills

    response.write(json.dumps(message))

    return response

@csrf_exempt
@require_POST
def user(request):
    response = HttpResponse()

    if 'method' not in request.POST or request.POST['method'] is '' or \
        'password' not in request.POST or request.POST['password'] is '' or \
        'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '' :
        if 'method' not in request.POST or request.POST['method'] is '':
            response.write("No Method")
            return response
        if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '' :
            response.write("No Session")
            return response
        if 'password' not in request.POST or request.POST['password'] is '' :
            response.write("Missing")
            return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if user.count() is not 1:
        response.write("No Session")
        return response

    user = user.get()

    if check_password(request.POST['password'], user.password) is False:
        response.write("False")
        return response

    if request.POST['method'] == 'PATCH':

        errors = []
        if 'fname' in request.POST and request.POST['fname'] is not '' :
            user.fname = request.POST['fname']

        if 'lname' in request.POST and request.POST['lname'] is not '' :
            user.lname = request.POST['lname']
        
        #   Check username is not in use first
        if 'username' in request.POST and request.POST['username'] is not '' :
            if User.objects.filter(username = request.POST['username']).count() is 0:
                user.username = request.POST['username']
            else:
                errors.append("Duplicate Username")

        #   Check new password reaches minimum length
        if 'newpassword' in request.POST and request.POST['newpassword'] is not '' :
            if len(request.POST['newpassword']) >= 12:
                user.username = make_password(request.POST['newpassword'])
            else:
                errors.append("Password Short")
        
        #   Validate email
        #   Check email is not already in use
        #   Send email to old email and new email
        if 'email' in request.POST and request.POST['email'] is not '' :
            email = re.search(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", request.POST['email'], flags=re.I).group()
            if email is not None:
                if User.objects.filter(email = email).count() is 0:
                    messageOld = "Your HobbyShare.app account email has been changed to:\n"
                    messageOld += request.POST['email']
                    messageNew = "Your HobbyShare.app account email has been changed from:\n"
                    messageNew += user.email

                    send_mail(
                        'Changed HobbyShare.app Email Address',
                        messageOld,
                        'no-reply@hobbyshare.app',
                        [user.email],
                        fail_silently = True,
                        )

                    user.email = request.POST['email']

                    try:
                        send_mail(
                        'Changed HobbyShare.app Email Address',
                        messageNew,
                        'no-reply@hobbyshare.app',
                        [user.email],
                        fail_silently = False,
                        )
                    except (smtplib.SMTPException, smtplib.SMTPRecipientsRefused) as e:
                        response.write("Bad Email")
                else:
                    errors.append("Duplicate Email")
            else:
                errors.append("Bad Email")

        if 'skills' in request.POST and request.POST['skills'] is not '':
            user.skills = request.POST['skills']

        #   Check profilepic in files
        if 'profilepic' in request.FILES:
            if request.FILES['profilepic'].size > 1048576:
                errors.append("File Too Big")
            else:
                if bool(user.profilepic):
                    try:
                        os.remove(user.profilepic.path)
                    except OSError:
                        pass
                user.profilepic = request.FILES['profilepic']

        user.save()

        if len(errors) is 0:
            response.write("True")
        else:
            response.write(json.dumps(errors))

    elif request.POST['method'] == 'DELETE':

        # delete profile pic if there is one

        if bool(user.profilepic):
            try:
                os.remove(user.profilepic.path)
            except OSError:
                pass
        
        # delete all images in those projects if they have any
        # delete all projects owned by user
        projects = Project.objects.filter(owner = user)
        for project in projects:
            if bool(project.res1):
                try:
                    os.remove(project.res1.path)
                except OSError:
                    pass
            if bool(project.res2):
                try:
                    os.remove(project.res2.path)
                except OSError:
                    pass
            project.delete()

        message = "Your HobbyShare.app account has been deleted."
        send_mail(
            'Account Deleted',
            message,
            'no-reply@hobbyshare.app',
            [user.email],
            fail_silently = True,
        )

        user.delete()
        response.write("True")

    return response

@csrf_exempt
@require_POST
def make_project(request):
    response = HttpResponse()

    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '':
        response.write("No Session")
        return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    
    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    if 'name' not in request.POST or request.POST['name'] is '' or \
        'purpose' not in request.POST or request.POST['purpose'] is '' or \
        'plan' not in request.POST or request.POST['plan'] is '' or \
        'skills' not in request.POST or request.POST['skills'] is '' or \
        'status' not in request.POST or request.POST['status'] is '':

        missing = []
        if 'name' not in request.POST or request.POST['name'] is '':
            missing.append("name")
        if 'purpose' not in request.POST or request.POST['purpose'] is '':
            missing.append("purpose")
        if 'plan' not in request.POST or request.POST['plan'] is '':
            missing.append("plan")
        if 'skills' not in request.POST or request.POST['skills'] is '':
            missing.append("skills")
        if 'status' not in request.POST or request.POST['status'] is '':
            missing.append("status")
        response.write(json.dumps(missing))
        return response

    res1 = None
    res2 = None

    if 'res1' in request.FILES:
        res1 = request.FILES['res1']
    elif 'res1' not in request.FILES and 'res2' in request.FILES:
        res1 = request.FILES['res2']

    if 'res2' in request.FILES and res1 is not None:
        res2 = request.FILES['res2']

    res1 = request.FILES['res1'] if 'res1' in request.FILES else None

    #   Reject request if included picture is larger than 1 MB
    if res1 is not None and res1.size > 1048576:
        response.write("Res1 Too Big")
        return response

    if res2 is not None and res2.size > 1048576:
        response.write("Res2 Too Big")
        return response

    project = Project.objects.create(
        name = request.POST['name'],
        purpose = request.POST['purpose'],
        plan = request.POST['plan'],
        skills = request.POST['skills'],
        status = request.POST['status'],
        res1 = res1,
        res2 = res2,
        owner = user,
        requests = json.dumps([]),
        invites = json.dumps([]),
        contributors = json.dumps([])
        )

    projects = user.projects

    if user.projects is None:
        projects = []
    else:
        projects = json.loads(user.projects)

    projects.append(project.id)

    user.projects = json.dumps(projects)
    user.save()

    response.write("True")
    return response

@require_GET
def fetch_last_project(request):
    response = HttpResponse()

    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '':
        response.write("No Session")
        return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()
    project = Project.objects.filter(owner=user).order_by('-date_created')
    if project.count() is 0:
        response.write("False")
        return response
    
    project = project[0]
    response.write(project.id)

    return response

@require_GET
def get_project(request, id):
    response = HttpResponse()
    message = {}

    project = Project.objects.filter(id = id)
    if project.count() is not 1:
        response.write("False")
        return response

    project = project.get()

    if bool(project.res1) is True:
        with open(project.res1.path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            message["res1"] = image_data

    if bool(project.res2) is True:
        with open(project.res2.path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            message["res2"] = image_data

    message["name"] = project.name
    message["purpose"] = project.purpose
    message["plan"] = project.plan
    message["skills"] = project.skills
    message["status"] = project.status

    message["owner"] = project.owner.username

    if project.contributors is not None:
        ids = json.loads(project.contributors)
        usernames = []
        for id in ids:
            user = User.objects.filter(id = id)
            if user.count() is 1:
                user = user.get()
                usernames.append(user.username)
        message["contributors"] = json.dumps(usernames)
    else:
        message["contributors"] = project.contributors
        

    date_created = str(project.date_created.month) + "/" + str(project.date_created.day) + "/" + str(project.date_created.year) + " " \
        + str(project.date_created.hour) + ":"

    if project.date_created.minute < 10:
        date_created += "0" + str(project.date_created.minute)
    else:
        date_created += str(project.date_created.minute)

    last_updated = str(project.last_updated.month) + "/" + str(project.last_updated.day) + "/" + str(project.last_updated.year) + " " \
        + str(project.last_updated.hour) + ":"

    if project.last_updated.minute < 10:
        last_updated += "0" + str(project.last_updated.minute)
    else:
        last_updated += str(project.last_updated.minute)

    message["date_created"] = date_created
    message["last_updated"] = last_updated
    
    if 'sessionid' in request.COOKIES and request.COOKIES.get('sessionid') is not '':
        user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'), id = project.owner.id)
        if user.count() is 1:
            user = user.get()
            message["match"] = "Owner"
        else:
            flag = True
            for id in json.loads(project.contributors):
                user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'), id = id)
                if user.count() is 1:
                    message["match"] = "Contributor"
                    flag = False
            if flag:
                message["match"] = "False"
    else:
        message["match"] = "False"
    #
    # mesaage["match"]
    # Owner
    # Contributor
    # False

    response.write(json.dumps(message))
    return response

@csrf_exempt
def project(request, id):
    if request.method == "GET":
        return get_project(request, id)

    response = HttpResponse()

    if 'method' not in request.POST or request.POST['method'] is '':
        response.write("No Method")
        return response

    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '':
        response.write("No Session")
        return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if user.count() is not 1:
        response.write("No Session")
        return response

    user = user.get()
    project = Project.objects.filter(id = id, owner = user)
    if project.count() is not 1:
        response.write("False")
        return response

    project = project.get()

    if request.POST['method'] == "PATCH":
        if 'name' in request.POST and request.POST['name'] is not '':
            project.name = request.POST['name']
        
        if 'purpose' in request.POST and request.POST['purpose'] is not '':
            project.purpose = request.POST['purpose']

        if 'plan' in request.POST and request.POST['plan'] is not '':
            project.plan = request.POST['plan']

        if 'skills' in request.POST and request.POST['skills'] is not '':
            project.skills = request.POST['skills']

        if 'status' in request.POST and request.POST['status'] is not '':
            project.status = request.POST['status']

        if 'res1' in request.FILES:
            if request.FILES['res1'].size > 1048576:
                response.write("Res1 Too Big")
                return response
            else:
                if bool(project.res1):
                    try:
                        os.remove(project.res1.path)
                    except OSError:
                        pass
                project.res1 = request.FILES['res1']

        if 'res2' in request.FILES and 'res1' not in request.FILES:
            if request.FILES['res2'].size > 1048576:
                response.write("Res2 Too Big")
                return response
            else:
                if bool(project.res1):
                    try:
                        os.remove(project.res1.path)
                    except OSError:
                        pass
                project.res1 = request.FILES['res2']

        if 'res2' in request.FILES and 'res1' in request.FILES:
            if request.FILES['res2'].size > 1048576:
                response.write("Res2 Too Big")
                return response
            else:
                if bool(project.res2):
                    try:
                        os.remove(project.res2.path)
                    except OSError:
                        pass
                project.res2 = request.FILES['res2']

        project.save()
        response.write("True")

    elif request.POST['method'] == "DELETE":
        if bool(project.res1):
            try:
                os.remove(project.res1.path)
            except OSError:
                pass
        if bool(project.res2):
            try:
                os.remove(project.res2.path)
            except OSError:
                pass

        project.delete()

        response.write("True")

    return response

@csrf_exempt
@require_POST
def join_request(request):
    response = HttpResponse()

    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '' or \
        'id' not in request.POST or request.POST['id'] is '':
        response.write("No Session")
        return response

    #find user through sessionid
    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if user.count() is not 1:
        response.write("No Session")
        return response

    user = user.get()

    project = Project.objects.filter(id = request.POST['id'])
    if project.count() is not 1:
        response.write("False")
        return response

    project = project.get()

    if project.requests is None:
        request_list = []
    else:
        request_list = json.loads(project.requests)

    if user.id in request_list:
        response.write("True")
        return response

    request_list.append(user.id)

    if project.invites is None:
        invite_list = []
    else:
        invite_list = json.loads(project.invites)

    if project.contributors is None:
        contributors = []
    else:
        contributors = json.loads(project.contributors)

    if user.contributing is None:
        contributing = []
    else:
        contributing = json.loads(user.contributing)

    owner = User.objects.get(id = project.owner.id)

    #check if user is in both request list and invite list
    for i in range(len(request_list)):
        for j in range(len(invite_list)):
            #   if yes then remove from both and put on contributor list
            if j < len(invite_list) and i < len(request_list) and request_list[i] == invite_list[j] and user.id == invite_list[j]:

                contributing.append(project.id)
                user.contributing = json.dumps(contributing)
                contributors.append(request_list[i])
                del request_list[i]
                del invite_list[j]
                #   email both about new contributor
                messageOwner = "Your project "
                messageOwner += project.name
                messageOwner += " has a new contributor: "
                messageOwner += user.username
                messageOwner += "!"

                messageUser = "You are now a contributor to "
                messageUser += owner.username
                messageUser += "'s "
                messageUser += project.name
                messageUser += "!"

                send_mail(
                    'New Contributor',
                     messageOwner,
                     'no-reply@hobbyshare.app',
                     [owner.email],
                     fail_silently = True,
                )

                send_mail(
                    'New Contributor',
                     messageUser,
                     'no-reply@hobbyshare.app',
                     [user.email],
                     fail_silently = True,
                )

    #   if no then email owner about contributor request
    if user.id in request_list:
        messageOwner = user.username
        messageOwner += " is requesting to be a contributor to your project "
        messageOwner += project.name
        messageOwner += "."

        send_mail(
            'New Contributor Request',
            messageOwner,
            'no-reply@hobbyshare.app',
            [owner.email],
            fail_silently = True,
        )

    project.requests = json.dumps(request_list)
    project.invites = json.dumps(invite_list)
    project.contributors = json.dumps(contributors)
    project.save()
    user.save()

    response.write("True")

    return response

@csrf_exempt
@require_POST
def invite(request):
    response = HttpResponse()

    if 'username' not in request.POST or request.POST['username'] is '' or \
        'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '' or \
        'id' not in request.POST or request.POST['id'] is '':
        response.write("False")
        return response

    owner = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if owner.count() is not 1:
        response.write("No Session")
        return response

    owner = owner.get()

    project = Project.objects.filter(owner = owner, id = request.POST['id'])
    if project.count() is not 1:
        response.write("False")
        return response

    project = project.get()

    #find user through username
    user = User.objects.filter(username = request.POST['username'])
    if user.count() is not 1:
        response.write("False")
        return response
    
    user = user.get()

    if project.requests is None:
        request_list = []
    else:
        request_list = json.loads(project.requests)

    if project.invites is None:
        invite_list = []
    else:
        invite_list = json.loads(project.invites)

    if user.id in invite_list:
        response.write("True")
        return response

    #add user id to invite list
    invite_list.append(user.id)

    if project.contributors is None:
        contributors = []
    else:
        contributors = json.loads(project.contributors)

    if user.contributing is None:
        contributing = []
    else:
        contributing = json.loads(user.contributing)

    for i in range(len(invite_list)):
        for j in range(len(request_list)):
            #check if user is in both request list and invite 
            if i < len(invite_list) and j < len(request_list) and invite_list[i] == request_list[j] and user.id == request_list[j]:
                
                contributing.append(project.id)
                user.contributing = json.dumps(contributing)
                contributors.append(request_list[j])
                del request_list[j]
                del invite_list[i]
                #   email both about new contributor
                messageOwner = "Your project "
                messageOwner += project.name
                messageOwner += " has a new contributor: "
                messageOwner += user.username
                messageOwner += "!"

                messageUser = "You are now a contributor to "
                messageUser += owner.username
                messageUser += "'s "
                messageUser += project.name
                messageUser += "!"

                send_mail(
                    'New Contributor',
                     messageOwner,
                     'no-reply@hobbyshare.app',
                     [owner.email],
                     fail_silently = True,
                )

                send_mail(
                    'New Contributor',
                     messageUser,
                     'no-reply@hobbyshare.app',
                     [user.email],
                     fail_silently = True,
                )

    #   if no then email user about invite
    if user.id in invite_list:
        messageUser = owner.username
        messageUser += " is inviting you to their project "
        messageUser += project.name
        messageUser += "."

        send_mail(
            'New Contributor Invite',
             messageUser,
            'no-reply@hobbyshare.app',
            [user.email],
            fail_silently = True,
        )

    project.requests = json.dumps(request_list)
    project.invites = json.dumps(invite_list)
    project.contributors = json.dumps(contributors)
    project.save()
    user.save()

    response.write("True")

    return response

@csrf_exempt
@require_POST
def leave(request):
    response = HttpResponse()

    if 'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '' or \
        'id' not in request.POST or request.POST['id'] is '':
        response.write("False")
        return response

    #find user through sessionid
    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    project = Project.objects.filter(id = request.POST['id'])
    if project.count() is not 1:
        response.write("False")
        return response

    project = project.get()

    if project.requests is None:
        request_list = []
    else:
        request_list = json.loads(project.requests)

    if project.invites is None:
        invite_list = []
    else:
        invite_list = json.loads(project.invites)

    if project.contributors is None:
        contributors = []
    else:
        contributors = json.loads(project.contributors)

    if user.contributing is None or user.contributing == 'null':
        contributing = []
    else:
        contributing = json.loads(user.contributing)

    #remove user from all three lists
    if user.id in request_list:
        request_list.remove(user.id)
    if user.id in invite_list:
        invite_list.remove(user.id)
    if user.id in contributors:
        contributors.remove(user.id)
    if project.id in contributing:
        contributing.remove(project.id)
        user.contributing = json.dumps(contributing)

    project.requests = json.dumps(request_list)
    project.invites = json.dumps(invite_list)
    project.contributors = json.dumps(contributors)
    project.save()
    user.save()

    response.write("True")

    return response

@csrf_exempt
@require_POST
def fetch_projects(request):
    response = HttpResponse()

    if 'ids' not in request.POST or request.POST['ids'] is '' or request.POST['ids'] == 'null':
        return response
    projects = []

    ids = json.loads(request.POST['ids'])
    for i in range(len(ids)):
        project = Project.objects.filter(id = ids[i])
        if project.count() is not 1:
            continue
        project = project.get()

        # create json
        data = {}
        data['name'] = project.name
        data['owner'] = project.owner.username
        data['status'] = project.status
        data['id'] = project.id

        date_created = str(project.date_created.month) + "/" + str(project.date_created.day) + "/" + \
            str(project.date_created.year) + " " + str(project.date_created.hour) + ":"

        if project.date_created.minute < 10:
            date_created += "0" + str(project.date_created.minute)
        else:
            date_created += str(project.date_created.minute)

        last_updated = str(project.last_updated.month) + "/" + str(project.last_updated.day) + "/" + \
            str(project.last_updated.year) + " " + str(project.last_updated.hour) + ":"

        if project.last_updated.minute < 10:
            last_updated += "0" + str(project.last_updated.minute)
        else:
            last_updated += str(project.last_updated.minute)

        data["date_created"] = date_created
        data["last_updated"] = last_updated

        if bool(project.res1) is True:
            with open(project.res1.path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                data["res1"] = image_data

        # turn into string
        data = json.dumps(data)

        # append to array
        projects.append(data)

    response.write(json.dumps(projects))
    return response

@csrf_exempt
@require_GET
def recent(request):
    response = HttpResponse()
    # return array of last 20 created project ids

    projects = Project.objects.all().order_by("-date_created")

    ids = []

    for i in range(len(projects)):
        if i < 21 :
            ids.append(projects[i].id)

    response.write(json.dumps(ids))

    return response

@csrf_exempt
def remove(request):
    response = HttpResponse()

    if 'username' not in request.POST or request.POST['username'] is '' or \
        'sessionid' not in request.COOKIES or request.COOKIES.get('sessionid') is '' or \
        'id' not in request.POST or request.POST['id'] is '':
        response.write("False")
        return response

    owner = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if owner.count() is not 1:
        response.write("No Session")
        return response

    owner = owner.get()

    project = Project.objects.filter(owner = owner, id = request.POST['id'])
    if project.count() is not 1:
        response.write("False")
        return response

    project = project.get()

    #find user through username
    user = User.objects.filter(username = request.POST['username'])
    if user.count() is not 1:
        response.write("False")
        return response
    
    user = user.get()

    if project.requests is None:
        request_list = []
    else:
        request_list = json.loads(project.requests)

    if project.invites is None:
        invite_list = []
    else:
        invite_list = json.loads(project.invites)

    if project.contributors is None:
        contributors = []
    else:
        contributors = json.loads(project.contributors)

    if user.contributing is None or user.contributing == 'null':
        contributing = []
    else:
        contributing = json.loads(user.contributing)

    #remove user from all three lists
    if user.id in request_list:
        request_list.remove(user.id)
    if user.id in invite_list:
        invite_list.remove(user.id)
    if user.id in contributors:
        contributors.remove(user.id)
    if project.id in contributing:
        contributing.remove(project.id)
        user.contributing = json.dumps(contributing)

    project.requests = json.dumps(request_list)
    project.invites = json.dumps(invite_list)
    project.contributors = json.dumps(contributors)
    project.save()
    user.save()

    response.write("True")

    return response