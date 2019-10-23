from django.test import TestCase
from .models import Session, Machine, Material
from .forms import SessionForm
from django.urls import reverse
from .views import test_switch
from authentication.models import User

# Create your tests here.


class SessionTests():
    fixtures = ['test_data.json', ]

    def setUp(self) -> None:
        self.client.login(email="someuser2@somedomain.com", password="CU&7rPE=(SCg:Zx{")

    def test_models_loaded(self):
        self.assertTrue(Material.objects.get(pk=2))
        self.assertTrue(Machine.objects.get(pk=1))
        self.assertTrue(Session.objects.get(pk=18))

    def test_session_view_exists(self):
        response = self.client.get('/sessions/18/')
        self.assertEqual(response.status_code, 200)

    def test_session_test_switch(self):
        test_list = ["01", "03", "08", "05", "13"]
        for test in test_list:
            response = self.client.get(reverse('test_switch', kwargs={"pk": 18, "number": test}))
            self.assertRedirects(response, "/sessions/18/")

    def test_create_new_session(self):
        machine = Machine.objects.get(pk=1)
        material = Material.objects.get(pk=2)
        response = self.client.post(reverse("new_session"),
                                    {'name': "Untitled", "material": material, "machine": machine,
                                     "target": "mechanical_strength"})
        self.assertRedirects(response, "/sessions/20/")
