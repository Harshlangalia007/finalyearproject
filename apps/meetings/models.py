from django.db import models
from django.contrib.auth.models import User

class Meeting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50) # e.g., 'audio', 'text', 'manual'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
