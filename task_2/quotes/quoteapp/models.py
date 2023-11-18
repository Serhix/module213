from django.db import models


# Create your models here.


class Tag(models.Model):
    name = models.CharField(max_length=50, null=False, unique=True)

    def __str__(self):
        return f"{self.name}"


class Author(models.Model):
    fullname = models.CharField(max_length=60, null=False)
    born_date = models.DateField(null=False)
    born_location = models.CharField(max_length=100, null=False)
    description = models.CharField(max_length=4500, null=False)

    def __str__(self):
        return f"{self.fullname}"


class Quote(models.Model):
    quote = models.CharField(max_length=2500, null=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return f"{self.quote[0:20]}..."
