from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class File_Type(models.Model):
    name = models.CharField(max_length=5)

    def __str__(self):
        return self.name

class User_Doc(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fileName = models.CharField(max_length=255)
    fileType = models.ForeignKey(File_Type, on_delete=models.CASCADE)
    file = models.FileField(upload_to='docs/')
    fileSize = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

    # def delete(self, *args, **kwargs):
    #     self.file.delete()
    #     super().delete(*args, **kwargs)
