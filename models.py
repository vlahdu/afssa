from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class MediaUpload(models.Model):
    CATEGORY_CHOICES = [
        ('wav2lip', 'Wav2Lip'),
        ('sadtalker', 'SadTalker'),
        ('makeittalk', 'MakeItTalk'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='wav2lip')
    audio = models.FileField(upload_to='audio/', blank=True, null=True)
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    public = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Rating(models.Model):
    video = models.ForeignKey(MediaUpload, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    facial_inconsistencies = models.FloatField(default=1)
    glitches_or_artifacts = models.FloatField(default=1)
    background_quality = models.FloatField(default=1)
    lip_sync_accuracy = models.FloatField(default=1)
    overall_score = models.FloatField(default=1, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        unique_together = ('video', 'user', 'is_public')

    def __str__(self):
        return f"{self.overall_score} for {self.video} by {self.user}"
