from django.contrib.auth.models import User
from django.db import models

class College(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    application_deadline = models.DateField()
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['application_deadline']


class Application(models.Model):
    STATUS_CHOICES = [
        ('researching', 'Researching'),
        ('applying', 'Applying'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('deferred', 'Deferred'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='researching')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.college.name}"

    class Meta:
        unique_together = ['user', 'college']


class Task(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date', 'created_at']
