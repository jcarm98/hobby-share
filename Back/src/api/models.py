from django.db import models

class User(models.Model):
    fname = models.CharField(max_length=20)
    lname = models.CharField(max_length=20)
    username = models.CharField(max_length=20)
    password = models.TextField()
    email = models.CharField(max_length=30)
    skills = models.TextField()
    
    profilepic = models.ImageField(upload_to='profilepics', null=True)

    projects = models.TextField(null=True)
    contributing = models.TextField(null=True)

    sessionid = models.TextField(null=True)
    token = models.TextField(null=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Project(models.Model):
    name = models.CharField(max_length=50)
    purpose = models.TextField()
    plan = models.TextField()
    skills = models.TextField()
    status = models.CharField(max_length=20)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(
        'User',
         on_delete=models.CASCADE
         )
    contributors = models.TextField(null=True)

    res1 = models.ImageField(upload_to='resource1', null=True)
    res2 = models.ImageField(upload_to='resource2', null=True)

    requests = models.TextField(null=True)
    invites = models.TextField(null=True)

    def __str__(self):
        return self.name
