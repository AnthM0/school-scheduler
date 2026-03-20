from django.db import models

DAYS_OF_WEEK = [
    ('monday', 'Monday'),
    ('tuesday', 'Tuesday'),
    ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'),
    ('friday', 'Friday'),
]

SUBJECTS = [
    ('math', 'Math'),
    ('history', 'History'),
    ('science', 'Science'),
    ('english', 'English'),
    ('language', 'Language'),
    ('other', 'Other'),
]

ROLES = [
    ('superuser', 'SuperUser'),
    ('admin', 'Admin'),
    ('teacher', 'Teacher'),
    ('student', 'Student'),
]

class Group(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subgroups'
    )
    monday = models.ManyToManyField('Class', blank=True, related_name='monday_groups')
    tuesday = models.ManyToManyField('Class', blank=True, related_name='tuesday_groups')
    wednesday = models.ManyToManyField('Class', blank=True, related_name='wednesday_groups')
    thursday = models.ManyToManyField('Class', blank=True, related_name='thursday_groups')
    friday = models.ManyToManyField('Class', blank=True, related_name='friday_groups')

    class Meta:
        ordering = ['name']

    def __str__(self):
        names = [self.name]
        parent = self.parent
        while parent is not None:
            names.insert(0, parent.name)
            parent = parent.parent
        return ' → '.join(names)

class Class(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=20, choices=SUBJECTS, default='other')
    start_time = models.TimeField()
    end_time = models.TimeField()
    minutes = models.PositiveIntegerField(editable=False, default=0)

    class Meta:
        ordering = ['start_time']

    def save(self, *args, **kwargs):
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        self.minutes = int((end - start).total_seconds() // 60)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.start_time:%I:%M %p} - {self.end_time:%I:%M %p}, {self.minutes} mins)"
    
class UserProfile(models.Model):
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(max_length=20, choices=ROLES, default='student')
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='members'
    )

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"