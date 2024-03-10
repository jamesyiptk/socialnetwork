from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    text = models.CharField(max_length=200)
    creation_time = models.DateTimeField()

    def __str__(self):
        return f'id={self.id}, text="{self.text}"'


class Comment(models.Model):
    text = models.CharField(max_length=200)
    creation_time = models.DateTimeField()
    creator = models.ForeignKey(User, default=None, on_delete=models.PROTECT)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    bio = models.CharField(max_length=200)
    picture = models.FileField(blank=True)
    content_type = models.CharField(max_length=50, blank=True)
    following = models.ManyToManyField(User, related_name='followers')

    def __str__(self):
        return f'id={self.id}'
