from django import forms
from .models import UploadedFile


class MultipleUploadForm(forms.ModelForm):
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}),
                            label='Выберите файлы')

    class Meta:
        model = UploadedFile
        fields = []

    def save(self, commit=True):

        files = self.cleaned_data.get('files')
        save_objects = []

        for file in files:
            file_name = file.name

            instance = UploadedFile(
                file=file,
                title=file_name
            )
            if commit:
                instance.save()
            save_objects.append(instance)

        return save_objects
