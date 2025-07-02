from django.db import models

class Page(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    name = models.CharField(max_length=255)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="sections")

    def __str__(self):
        return f"{self.page.name} - {self.name}"


class Ad(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="ads")
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="ads/", blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Ad in {self.section.name} - {self.title}"


class Attribute(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class AdAttributeValue(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="attributes")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.TextField()

    class Meta:
        unique_together = ("ad", "attribute")

    def __str__(self):
        return f"{self.ad.title} - {self.attribute.name}: {self.value}"
