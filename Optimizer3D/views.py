from django.shortcuts import render, get_object_or_404, redirect
from rosetta.views import TranslationFormView
from difflib import unified_diff as diff
import io
from messaging import email
from datetime import datetime
from os.path import relpath


def index(request):
    return redirect('session:index')

class CustomTranslationFormView(TranslationFormView):
    def post(self, request, *a, **k):
        file_path = self.po_file_path
        with open(file_path) as f:
            before_submit = f.readlines()

        result = super().post(request, *a, **k)

        with open(file_path) as f:
            after_submit = f.readlines()

        if before_submit != after_submit:
            with io.StringIO() as patch_file:
                patch_file.writelines(diff(before_submit, 
                                           after_submit, 
                                           fromfile='a/'+relpath(file_path),
                                           tofile='b/'+relpath(file_path)))

                patch_filename = f'{self.language_id}_{datetime.now():%y-%m-%d_%H:%M:%S}_{request.user.email}.patch'
                email.send_to_devs(
                        'translation_updated',
                        request,
                        [(patch_filename, patch_file.getvalue(), 'text/plain')],
                        patch_filename=patch_filename,
                        creator=request.user,
                        language=self.language_id
                        )

        return result
