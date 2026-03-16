from django.db import models
from apps.meetings.models import Meeting
from django.contrib.auth.models import User

class ActionItem(models.Model):
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='action_items')
    task = models.TextField()
    owner = models.CharField(max_length=255)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    trello_synced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task} - {self.priority}"

class TrelloCredential(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255)
    token = models.CharField(max_length=255)
    list_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Trello Credentials for {self.user.username}"
