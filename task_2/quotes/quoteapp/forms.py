from django.forms import ModelForm, CharField, TextInput, DateField, ChoiceField
from django import forms
from .models import Tag, Author, Quote
from datetime import date


class TagForm(ModelForm):
    name = CharField(min_length=3, max_length=25, required=True,
                     widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tag"}))

    class Meta:
        model = Tag
        fields = ['name']


class AuthorForm(ModelForm):
    fullname = CharField(min_length=8, max_length=50, required=True,
                         widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Full name"}))
    born_date = DateField(required=True,
                          widget=forms.SelectDateWidget(years=range(1, date.today().year)))
    born_location = CharField(min_length=5, max_length=50, required=True,
                              widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Born location"}))
    description = CharField(min_length=10, max_length=5000, required=True,
                            widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Description"}))

    class Meta:
        model = Author
        fields = ['fullname', 'born_date', 'born_location', 'description']


class QuoteForm(ModelForm):
    quote = CharField(min_length=10, max_length=5000, required=True,
                      widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Quote"}))
    author = CharField(required=True, widget=forms.Select(attrs={"class": "form-control"}))
    tags = CharField(required=True, widget=forms.Select(attrs={"class": "form-control"}))

    class Meta:
        model = Quote
        fields = ['quote', 'author']
        exclude = ['tags']