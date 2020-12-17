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
                      httponly=True,
                      #samesite='None'
                      )

# Takes: attr (string), request (HttpRequest)
# Returns: True if attr is not in the HttpRequest POST form data, or if it is but it is empty or null, False otherwise
def missing(attr, request):
    return attr not in request.POST or request.POST[attr] is "" or request.POST[attr] == "null"

# Takes: attr (string), request (HttpRequest)
# Returns: True if there is a non-empty, non-null attribute attr in the HttpRequest POST form data, False otherwise
def has(attr, request):
    return attr in request.POST and request.POST[attr] is not "" and request.POST[attr] != "null"

# Takes: request (HttpRequest)
# Returns: True if cookie named sessionid does not exist in HttpRequest COOKIES or it is empty, False otherwise
def missingSession(request):
    return "sessionid" not in request.COOKIES or request.COOKIES.get("sessionid") is ""

# Takes: request (HttpRequest)
# Returns: True if cookie named sessionid exists in HttpRequest COOKIES and it is not empty, False otherwise
def hasSession(request):
    return "sessionid" in request.COOKIES and request.COOKIES.get("sessionid") is not ""

def usernameTaken(request):
    return User.objects.filter(username=request.POST['username']).count() > 0

def usernameFree(request):
    return not usernameTaken(request)

def emailTaken(request):
    return User.objects.filter(email=request.POST['email']).count() > 0

# Perform regex check to validate email
def validateEmail(emailAddress):
    email = re.search(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", emailAddress, flags=re.I).group()
    return email is not None and email is emailAddress

def badEmail(emailAddress):
    return not validateEmail(emailAddress)

# Only use after appropriate checks have been done
def userByUsername(request):
    return User.objects.filter(username = request.POST['username'], verified = True).get()

# Takes: Django DateTime object
# Returns: Formatted date (string)
def formatDate(dateTime):
    processed = str(dateTime.month) + "/" + str(dateTime.day) + "/" + str(dateTime.year) + " " \
    + str(dateTime.hour) + ":"

    if dateTime.minute < 10:
        processed += "0" + str(dateTime.minute)
    else:
        processed += str(dateTime.minute)

    return processed

# Takes: sessionid (cookie)
# Returns: "True" if valid session is found
#          "False" if no valid session is found
@csrf_exempt
@require_GET
def check_login(request):
    response = HttpResponse()
    
    if missingSession(request):
        response.write("False")
        return response

    # Exactly 1 user exists with present sessionid that is also verified
    if User.objects.filter(sessionid = request.COOKIES.get('sessionid'), verified = True).count() is 1:
        response.write("True")
    else:
        response.write("False")

    return response

# Takes: username (form data attribute)
# Returns: "True" if username is not found
#          "False" if username is found or missing from request
@csrf_exempt
@require_POST
def check_username(request):
    response = HttpResponse()

    if missing("username", request):
        response.write("False")
        return response

    # False if username is found
    if usernameTaken(request):
        response.write("False")
    else:
        response.write("True")

    return response
    
# Takes: email (form data attribute)
# Returns: "True" if email is not found
#          "False" if email is found
#          "Bad Email" if email does not pass initial validation
@csrf_exempt
@require_POST
def check_email(request):
    response = HttpResponse()

    if missing("email", request):
        response.write("Bad Email")
        return response

    if badEmail(request.POST['email']):
        response.write("Bad Email")
        return response

    # False if email is found
    if emailTaken(request):
        response.write("False")
    else:
        response.write("True")

    return response

# Takes: fname, lname, username, password, email (form data attributes), optional ?profilepic (form data file)
# Returns: "True" when all necessary data is present and no errors are raised
#          When returning "True" adds user to database and sends verification email
#          
#          Array of strings corresponding to missing data
#          e.g. ["fname", "lname", "username"]
#          
#          "Duplicate Username" when username is taken
#          "Password Short" when password received is shorter than 12 character minimum
#          "Bad Email" when email fails validation
#          "Duplicate Email" when email is taken
#          "File Too Big" when profilepic is larger than file size limit (1 MB)
@csrf_exempt
@require_POST
def sign_up(request):
    # Create HTTP response
    response = HttpResponse()

    # Check if all required fields are filled
    # If any are missing, return array of missing fields
    if missing("password", request) or missing("fname", request) or \
        missing("lname", request) or missing("username", request) or missing("email", request):

        missingData = []

        if missing("fname", request):
            missingData.append("fname")

        if missing("lname", request):
            missingData.append("lname")

        if missing("username", request):
            missingData.append("username")

        if missing("password", request):
            missingData.append("password")

        if missing("email", request):
            missingData.append("email")

        response.write(json.dumps(missingData))

        return response

    # Check if username is in use already
    if usernameTaken(request):
        response.write("Duplicate Username")
        return response

    # Check if password meets minimum length
    if len(request.POST['password']) < 12:
        response.write("Password Short")
        return response

    # Check if email address is in correct format
    if badEmail(request.POST['email']):
        response.write("Bad Email")
        return response

    # Check if email is in use already
    if emailTaken(request):
        response.write("Duplicate Email")
        return response

    # Hash and salt password
    password = make_password(request.POST['password'])

    # Generate authentication token
    token = get_random_string(length=32)

    # Extract optional image
    optionalPic = request.FILES['profilepic'] if 'profilepic' in request.FILES else None

    # Reject request if included picture is larger than 10 MB
    if optionalPic is not None and optionalPic.size > 1048576:
        response.write("File Too Big")
        return response

    # Compose email message
    message = 'Your HobbyShare.app Verification Token:\n\n%s\n\n' % token
    message += 'To verify your HobbyShare.app account:\n'
    message += '1. Copy the above token.\n'
    message += '2. Paste the token into the verification page: https://hobbyshare.app/verify/user/\n'
    message += '3. Click the verify button. You will receive a confirmation email when your account has been verified.\n'

    # Send verification email to user
    try:
        send_mail(
            'HobbyShare.app Verification',
            message,
            'no-reply@hobbyshare.app',
            [request.POST['email']],
            fail_silently = False,
        )
    except (smtplib.SMTPException, smtplib.SMTPRecipientsRefused) as e:
        response.write("Bad Email")
        return response

    # Create user in database
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

# Takes: token (form data attribute)
# Returns: "True" if token is valid
#          "False" if token is missing or invalid
@csrf_exempt
@require_POST
def verify_user(request):
    # Create HTTP response
    response = HttpResponse()

    # Check if token is present and valid
    if missing("token", request):
        response.write("False")
        return response

    user = User.objects.filter(token = request.POST['token'], verified = False)
    if user.count() is not 1:
        response.write("False")
        return response

    # Update verified boolean and remove token from user
    user = user.get()
    user.verified = True
    user.token = None;
    user.save()

    # Check for duplicate users and remove
    # Duplicates occur when user submits multiple sign-up requests in a short time frame
    duplicates = User.objects.filter(username = user.username, verified = False)
    duplicates.delete()

    response.write("True")
    return response

# Takes: username, password (form data attributes)
# Returns: "True" when username and password match
#          When returning "True" set sessionid cookie and store in database with user
#          
#          "False" when username and password do not match or either are missing
@csrf_exempt
@require_POST
def log_in(request):
    # Create HTTP response
    response = HttpResponse()

    # Check if all required fields are filled
    # Check if username is valid
    # If any are missing, return empty cookie
    if missing("username", request) or missing("password", request) or \
    User.objects.filter(username = request.POST['username'], verified = True).count() is not 1:
        response.write("False")
        return response

    # Check password
    # If not valid, return bad login
    user = userByUsername(request)
    if check_password(request.POST['password'], user.password) is False:
        response.write("False")
        return response

    # Create sessionid
    sessionid = get_random_string(length=128)

    # Store sessionid in database
    user.sessionid = sessionid
    user.save()

    response.write("True")

    # Store sessionid in cookie
    set_cookie(response, 'sessionid', sessionid)
    return response

# Takes: sessionid (cookie)
# Returns: HTTP 200
@csrf_exempt
@require_POST
def log_out(request):
    response = HttpResponse()

    #   Check if sessionid is present
    if missingSession(request):
        return response

    #   Find user with given sessionid
    user = User.objects.get(sessionid=request.COOKIES.get('sessionid'))
    #   Remove sessionid from database
    user.sessionid = None
    user.save()

    #   Remove sessionid from cookie
    set_cookie(response, 'sessionid', '')

    return response

# Takes: from, message, subject (form data attributes)
# Returns: "True" when from is a valid email and the email is sent without error
#          
#          Array of strings corresponding to missing data
#          e.g. ["from", "message", "subject"]
#          
#          "False" when email fails to send
#          "Bad Email" when from fails validation
@csrf_exempt
@require_POST
def email(request):
    response = HttpResponse()
    # Check if all required fields are filled
    # If any are missing, return array of missing fields
    if missing("from", request) or missing("message", request) or missing("subject", request):
        missingData = []

        if missing("subject", request):
            missingData.append("subject")

        if missing("from", request):
            missingData.append("from")

        if missing("message", request):
            missingData.append("message")

        response.write(json.dumps(missingData))
        return response

    # Check if email address is in correct format
    if badEmail(request.POST['from']):

        response.write("Bad Email")
        return response

    contactEmail = "joseph@splitreceipt.app"

    # Attempt to send email to our contact email address
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

# Takes: email (form data attribute)
# Returns: "True" always
#          When email is valid, sends an email with the user's username
@csrf_exempt
@require_POST
def forgot_user(request):
    response = HttpResponse()
    response.write("True")

    # Ignore if missing email
    if missing("email", request):
        return response

    # User by email
    user = User.objects.filter(email = request.POST['email'])
    if user.count() is not 1:
        return response

    # Only send email if 1 user is found
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

# Takes: username (form data attribute)
# Returns: "True" always
#          When username is valid, sends an email with a password reset token
@csrf_exempt
@require_POST
def forgot_password(request):
    response = HttpResponse()
    response.write("True")

    # Ignore if missing username
    if missing("username", request):
        return response

    # User by username
    user = User.objects.filter(username = request.POST['username'])
    if user.count() is not 1:
        return response

    # Generate authentication token
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

    # Send password reset email
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

# Takes: token, password (form data attributes)
# Returns: "True" when token is valid, and password is valid
#          When returning "True" an email is sent notifying the user that their password has changed
#          
#          Array of strings corresponding to missing data
#          e.g. ["token", "password"]
#          
#          "False" when token is invalid
#          "Password Short" when password does not meet 12 character minimum
#          "Fail" when password is successfully reset but the notification email has failed
@csrf_exempt
@require_POST
def reset_password(request):
    response = HttpResponse()
    
    if missing("token", request) or missing("password", request):

        missingData = []
        if missing("token", request):
            missingData.append("token")

        if missing("password", request):
            missingData.append("password")

        response.write(json.dumps(missingData))

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

# Takes: sessionid (cookie)
# Returns: the username that corresponds to the sessionid, if found
#          "False" when sessionid is missing or no user is found
@require_GET
def fetch_username(request):
    response = HttpResponse()
    
    # Check if sessionid is present
    if missingSession(request):
        response.write("False")
        return response

    # User by sessionid
    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))

    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    response.write(user.username)
    return response

# Takes: username (url param e.g. /usernamehere/)
# Returns: stringified json containing user information, if username is valid
#          "False" if user is not found
@require_GET
def get_user(request, username):
    response = HttpResponse()
    message = {}

    user = User.objects.filter(username = username)
    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    # Profile pic may not exist, but encode in base64 if it does
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

    # Only show email if user is logged in
    if hasSession(request) and \
        User.objects.filter(sessionid = request.COOKIES.get('sessionid'), verified = True).count() is 1:
        message["email"]=user.email

        # Set a boolean if the user is the owner of the profile
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

# Takes: sessionid (cookie)
# Returns: stringified json of user data, if found
#          "False" if no user is found
#          "No Session" if not logged in
@require_GET
def get_self(request):
    response = HttpResponse()

    if missingSession(request):
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

# Takes: sessionid (cookie), password (form data attribute), method (form data attribute, only "PATCH" or "DELETE")
# Returns: "True" when action is successful
#          "No Method" when request is missing method
#          "No Session" if not logged in
#          "False" if password is incorrect
#           
#          Array of errors, changes not listed in array are assumed to be successful
#          e.g. ["Duplicate Username", "Bad Email", "File Too Big"]
#               "Duplicate Username" if username is already in use
#               "Password Short" is password does not meet 12 character minimum
#               "Bad Email" if email fails validation
#               "Duplicate Email" if email is already in use
#               "File Too Big" if file exceeds 1MB file size
#          
#          When request passes validation, PATCH will attempt to update all provided attributes for user
#          When request passes validation, DELETE will delete the user account and attempt to email them
@csrf_exempt
@require_POST
def user(request):
    response = HttpResponse()

    if missing("method", request):
        response.write("No Method")
        return response

    if missingSession(request):
        response.write("No Session")
        return response

    if missing("password", request):
        response.write("Missing")
        return response
    
    # Find user with sessionid
    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if user.count() is not 1:
        response.write("No Session")
        return response

    user = user.get()

    # Check password
    if check_password(request.POST['password'], user.password) is False:
        response.write("False")
        return response

    # PATCH
    if request.POST['method'] == 'PATCH':
        return userPATCH(request, user, response)

    # DELETE
    elif request.POST['method'] == 'DELETE':
        return userDELETE(request, user, response)

    return response

# Takes: optional ?fname, ?lname, ?username, ?email, ?newpassword (form data attributes), ?profilepic (form data file)
# Returns: "True" when patch has no errors
#          When request passes validation, PATCH will attempt to update all provided attributes for user
#          
#          Array of errors, changes not listed in array are assumed to be successful
#          e.g. ["Duplicate Username", "Bad Email", "File Too Big"]
#               "Duplicate Username" if username is already in use
#               "Password Short" is password does not meet 12 character minimum
#               "Bad Email" if email fails validation
#               "Duplicate Email" if email is already in use
#               "File Too Big" if file exceeds 1MB file size
def userPATCH(request, user, response):
    errors = []
    
    if has("fname", request):
        user.fname = request.POST['fname']

    if has("lname", request):
        user.lname = request.POST['lname']

    # Check username is not in use first
    if has("username", request):
        if usernameFree(request):
            user.username = request.POST['username']
        else:
            errors.append("Duplicate Username")

    # Check new password reaches minimum length
    if has("newpassword", request):
        if len(request.POST['newpassword']) >= 12:
            user.password = make_password(request.POST['newpassword'])
        else:
            errors.append("Password Short")
        
    #   Validate email
    #   Check email is not already in use
    #   Send email to old email and new email
    if has("email", request):
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

    if has("skills", request):
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

    return response

# Takes: request (HttpRequest), user (User model), response (HttpResponse)
# Returns: "True" always
#          When returning "True", attempts to email the user and delete their account
def userDELETE(request, user, response):
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

        # Notify user of account deletion
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

# Takes: sessionid (cookie), name, purpose, plan, skills, status (form data attributes), optional ?res1, ?res2 (form data files)
# Returns: "True" when project creation is successful
#          When returning "True" creates project in database with owner as user that provided request
#          "No Session" if not logged in
#          "False" if no user is found with given session
#          "Res1 Too Big" if res1 file exceeds 1MB filesize
#          "Res2 Too Big" if res2 file exceeds 1MB filesize
#          
#          Array of strings corresponding to missing data
#          e.g. ["name", "skills", "status"]
@csrf_exempt
@require_POST
def make_project(request):
    response = HttpResponse()

    if missingSession(request):
        response.write("No Session")
        return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    
    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    if missing("name", request) or missing("purpose", request) or missing("plan", request) or \
        missing("skills", request) or missing("status", request):

        missingData = []
        if missing("name", request):
            missingData.append("name")

        if missing("purpose", request):
            missingData.append("purpose")

        if missing("plan", request):
            missingData.append("plan")

        if missing("skills", request):
            missingData.append("skills")

        if missing("status", request):
            missingData.append("status")

        response.write(json.dumps(missingData))
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

    # Reject request if included picture is larger than 1 MB
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

# Takes: sessionid (cookie)
# Returns: project id of the most recent project by that user
#          "No Session" if not logged in
#          "False" if no user is found with session or if user has no projects
@require_GET
def fetch_last_project(request):
    response = HttpResponse()

    if missingSession(request):
        response.write("No Session")
        return response

    user = User.objects.filter(sessionid = request.COOKIES.get('sessionid'))
    if user.count() is not 1:
        response.write("False")
        return response

    user = user.get()

    # Sort projects in descending order (newest first)
    project = Project.objects.filter(owner=user).order_by('-date_created')
    if project.count() is 0:
        response.write("False")
        return response
    
    project = project[0]
    response.write(project.id)

    return response

# Takes: id (url parameter e.g. /idnumber/)
# Returns: Stringified JSON of project data, if found
#          "False" if no project is found
@require_GET
def get_project(request, id):
    response = HttpResponse()

    # Attempt to find project with id in url
    project = Project.objects.filter(id = id)
    if project.count() is not 1:
        response.write("False")
        return response

    message = {}
    project = project.get()

    # If the project has a resource1
    if bool(project.res1) is True:
        # Use base64 encoding for sending image as a string
        with open(project.res1.path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            message["res1"] = image_data

    # Repeat with resource2
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

    # Return usernames of contributors
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

    message["date_created"] = formatDate(project.date_created)
    message["last_updated"] = formatDate(project.last_updated)
    
    # Determine if the project belongs to this user, or if they are a contributor
    if hasSession(request):
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

    response.write(json.dumps(message))
    return response

# Takes: method (form data attribute ), sessionid, id,
#        optional ?name, ?purpose, ?plan, ?skills, ?status (form data attributes),
#        ?res1, ?res2 (form data files)
# Returns: method == "GET": project information based on project id
#          method == "PATCH": "True" if successful, else array of error strings
#          When method == "PATCH" all data provided will be used to update project
#          
#          method == "DELETE": "True" always
#          
#          "No Session" if not logged in
#          "No Method" if method is missing
#          "False" if attempting to alter a project that is not owned by user
@csrf_exempt
def project(request, id):
    if request.method == "GET":
        return get_project(request, id)

    response = HttpResponse()

    if missing("method", request):
        response.write("No Method")
        return response

    if missingSession(request):
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

    # PATCH
    if request.POST['method'] == "PATCH":

        # Update any data that is provided
        if has("name", request):
            project.name = request.POST['name']
        
        if has("purpose", request):
            project.purpose = request.POST['purpose']

        if has("plan", request):
            project.plan = request.POST['plan']

        if has("skills", request):
            project.skills = request.POST['skills']

        if has("status", request):
            project.status = request.POST['status']

        # Check filesize
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

        # Put data in resource1 first
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

        # Only use resource2 when both are sent
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

    # DELETE
    elif request.POST['method'] == "DELETE":

        # Remove all images from database
        if bool(project.res1):
            try:
                os.remove(project.res1.path)
            except OSError:
                pass

        # Remove all images from database
        if bool(project.res2):
            try:
                os.remove(project.res2.path)
            except OSError:
                pass

        project.delete()

        response.write("True")

    return response

# Takes: sessionid (cookie), id (form data attribute)
# Returns: "True" if successful
#          When returning "True", user is added to either contributing list or request list
#          "No Session" if missing sessionid or id
#          "False" if no project is found
@csrf_exempt
@require_POST
def join_request(request):
    response = HttpResponse()

    if missingSession(request) or missing("id", request):
        response.write("No Session")
        return response

    # User by sessionid
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

    request_list = json.loads(project.requests)

    # User has already requested to join, do nothing
    if user.id in request_list:
        response.write("True")
        return response

    request_list.append(user.id)

    invite_list = json.loads(project.invites)
    contributors = json.loads(project.contributors)
    contributing = json.loads(user.contributing)
    
    owner = User.objects.get(id = project.owner.id)




    # check if user is in both request list and invite list
    for i in range(len(request_list)):
        for j in range(len(invite_list)):
            # if yes then remove from both and put on contributor list
            if j < len(invite_list) and i < len(request_list) and request_list[i] == invite_list[j] and user.id == invite_list[j]:

                contributing.append(project.id)
                user.contributing = json.dumps(contributing)
                contributors.append(request_list[i])
                del request_list[i]
                del invite_list[j]
                # email both about new contributor
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




    # If no then email owner about contributor request
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

# Takes: sessionid (cookie), id, username (form data attributes)
# Returns: "True" if successful
#          When returning "True", user is added to either contributing list or invite list
#          "No Session" if missing sessionid
#          "False" if no project or no player is found is found
@csrf_exempt
@require_POST
def invite(request):
    response = HttpResponse()

    if missing("username", request) or missingSession(request) or missing("id", request):
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

    # User by username
    user = User.objects.filter(username = request.POST['username'])
    if user.count() is not 1:
        response.write("False")
        return response
    
    user = user.get()

    request_list = json.loads(project.requests)
    invite_list = json.loads(project.invites)

    if user.id in invite_list:
        response.write("True")
        return response

    #add user id to invite list
    invite_list.append(user.id)

    contributors = json.loads(project.contributors)
    contributing = json.loads(user.contributing)



    # check if user is in both request list and invite list
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




    # If no then email user about invite
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

# Takes: sessionid (cookie), id (form data attribute)
# Returns: "True" if successful
#          When returning "True", user will be removed from the contributing list for the given project id
#          "False" if missing sessionid, user is not found, or project is not found
@csrf_exempt
@require_POST
def leave(request):
    response = HttpResponse()

    if missingSession(request) or missing("id", request):
        response.write("False")
        return response

    # User by sessionid
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
    request_list = json.loads(project.requests)
    invite_list = json.loads(project.invites)
    contributors = json.loads(project.contributors)
    contributing = json.loads(user.contributing)

    # Remove user from all three lists
    if user.id in request_list:
        request_list.remove(user.id)

    if user.id in invite_list:
        invite_list.remove(user.id)

    if user.id in contributors:
        contributors.remove(user.id)

    if project.id in contributing:
        contributing.remove(project.id)
        user.contributing = json.dumps(contributing)

    # Save changes
    project.requests = json.dumps(request_list)
    project.invites = json.dumps(invite_list)
    project.contributors = json.dumps(contributors)
    project.save()
    user.save()

    response.write("True")

    return response

# Takes: ids (form data attribute)
# Returns: Array of stringified json containing project data, if successful
#          HTTP 200 if ids is missing
@csrf_exempt
@require_POST
def fetch_projects(request):
    response = HttpResponse()

    if missing("ids", request):
        return response
    projects = []

    # Create json from each project and append to array
    ids = json.loads(request.POST['ids'])
    for i in range(len(ids)):
        project = Project.objects.filter(id = ids[i])
        if project.count() is not 1:
            continue
        project = project.get()

        # Create json
        data = {}
        data['name'] = project.name
        data['owner'] = project.owner.username
        data['status'] = project.status
        data['id'] = project.id
        data["date_created"] = formatDate(project.date_created)
        data["last_updated"] = formatDate(project.last_updated)

        # Optional resource
        if bool(project.res1) is True:
            with open(project.res1.path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                data["res1"] = image_data

        # Turn into string
        data = json.dumps(data)

        # Append to array
        projects.append(data)

    response.write(json.dumps(projects))
    return response

# Takes: request (HttpRequest)
# Returns: Array of project ids corresponding to the newest 20 projects
@require_GET
def recent(request):
    response = HttpResponse()

    projects = Project.objects.all().order_by("-date_created")

    ids = []

    for i in range(len(projects)):
        if i < 21 :
            ids.append(projects[i].id)

    response.write(json.dumps(ids))

    return response

# Takes: sessionid (cookie), id, username (form data attributes)
# Returns: "True" when succcessful
#          When returning "True", user with given username will be removed from the contributors list for project with given id
#          "No Session" if not logged in
#          "False" if missing username, id, sessionid, user is not found, or project is not found
@csrf_exempt
def remove(request):
    response = HttpResponse()

    if missing("username", request) or missingSession(request) or missing("id", request):
        response.write("False")
        return response

    # User by sessionid
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

    # User by username
    user = User.objects.filter(username = request.POST['username'])
    if user.count() is not 1:
        response.write("False")
        return response
    
    user = user.get()

    request_list = json.loads(project.requests)
    invite_list = json.loads(project.invites)
    contributors = json.loads(project.contributors)
    contributing = json.loads(user.contributing)

    # Remove user from all three lists
    if user.id in request_list:
        request_list.remove(user.id)

    if user.id in invite_list:
        invite_list.remove(user.id)

    if user.id in contributors:
        contributors.remove(user.id)

    if project.id in contributing:
        contributing.remove(project.id)
        user.contributing = json.dumps(contributing)

    # Save changes
    project.requests = json.dumps(request_list)
    project.invites = json.dumps(invite_list)
    project.contributors = json.dumps(contributors)
    project.save()
    user.save()

    response.write("True")

    return response