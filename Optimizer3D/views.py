from django.shortcuts import render, get_object_or_404, redirect
from rosetta.views import TranslationFormView
from difflib import unified_diff as diff
import io
from messaging import email
from datetime import datetime
from os.path import relpath
from django.utils.functional import cached_property
from polib import POEntry
from django.conf import settings
from django.utils.module_loading import import_string
import six
import hashlib


def index(request):
    return redirect('session:index')

class CustomTranslationFormView(TranslationFormView):
    @cached_property
    def po_file(self):
        pofile = super().po_file

        for (model_name, fields) in settings.LOCALIZABLE_MODELS:
            model = import_string(model_name)
            for unique_instance in model.objects.values(*fields).distinct():
                for field in fields:
                    msgid = unique_instance.get(field)
                    if msgid == '': continue

                    occurrence = ('.'.join((model_name, field)), '0')
                    entry = pofile.find(msgid)
                    if entry is None:
                        entry = POEntry(msgid=msgid)
                        str_to_hash = (
                                six.text_type(entry.msgid)
                                + six.text_type(entry.msgstr)
                                + six.text_type(entry.msgctxt or '')
                                ).encode('utf8')
                        entry.md5hash = hashlib.md5(str_to_hash).hexdigest()
                        pofile.append(entry)

                    if occurrence not in entry.occurrences:
                        entry.occurrences.append(occurrence)

        return pofile


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
