from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from session import models
from unittest.mock import Mock, patch
import re

class SessionMaterialViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.user = get_user_model().objects.create_user(email='known_user@somewhere.com',
                                 is_active=True,
                                 password='SomeSecretPassword')

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def test_material_detail(self):
        initial_name = 'Some personal test material'
        initial_size = 1.75

        material = models.Material.objects.create(name=initial_name, size_od=initial_size)

        edited_name = 'Another edited Material'
        edited_size = material.size_od + 1

        # should not be accessible, since user is not owner
        tst_url = reverse('material_detail', kwargs={'pk': material.pk})

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        resp = self.client.get(tst_url)
        self.assertEqual(404, resp.status_code)
        # should not be editable
        resp = self.client.post(tst_url, {'name': edited_name, 'size_od': edited_size})
        self.assertEqual(404, resp.status_code)

        material.refresh_from_db()
        self.assertTrue(material.owner != self.user)
        self.assertEqual(material.name, initial_name)
        self.assertEqual(material.size_od, initial_size)

        material.owner = self.user
        material.save()

        # should be accessible, since user is owner
        resp = self.client.get(tst_url)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(bytes(initial_name, 'utf-8') in resp.content)
        self.assertTrue(bytes(str(initial_size), 'utf-8') in resp.content)

        # should be editable
        edited_name = 'Another edited Material'
        edited_size = material.size_od + 1
        resp = self.client.post(tst_url, {'name': edited_name, 'size_od': edited_size})
        # post redirects to materials list
        self.assertEqual(302, resp.status_code)

        material.refresh_from_db()
        self.assertEqual(material.name, edited_name)
        self.assertEqual(material.size_od, edited_size)

        # updated data should be visible
        resp = self.client.get(tst_url)
        self.assertEqual(200, resp.status_code)
        self.assertTrue(bytes(edited_name, 'utf-8') in resp.content)
        self.assertTrue(bytes(str(edited_size), 'utf-8') in resp.content)

        material.delete()

        # should not be accessible, since material is gone
        resp = self.client.get(tst_url)
        self.assertEqual(404, resp.status_code)

        resp = self.client.post(tst_url, {'name': edited_name, 'size_od': edited_size})
        self.assertEqual(404, resp.status_code)

    def test_materials_view(self):
        name = 'Some personal test material'
        size = 1.75

        material = models.Material.objects.create(name=name, size_od=size)
        details_url = reverse('material_detail', kwargs={'pk': material.pk})
        delete_url = reverse('material_delete', kwargs={'pk': material.pk})

        # Should not show materials from other users
        tst_url = reverse('material_manager')

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        resp = self.client.get(tst_url)

        self.assertEqual(200, resp.status_code)
        self.assertFalse(bytes(name, 'utf-8') in resp.content)
        self.assertFalse(bytes(str(size), 'utf-8') in resp.content)
        self.assertFalse(bytes(details_url, 'utf-8') in resp.content)
        self.assertFalse(bytes(delete_url, 'utf-8') in resp.content)

        # should show materials from current user
        material.owner = self.user
        material.save()

        resp = self.client.get(tst_url)

        self.assertEqual(200, resp.status_code)
        self.assertTrue(bytes(name, 'utf-8') in resp.content)
        self.assertTrue(bytes(str(size), 'utf-8') in resp.content)
        self.assertTrue(bytes(details_url, 'utf-8') in resp.content)
        self.assertTrue(bytes(delete_url, 'utf-8') in resp.content)

        # should not show material after deletion
        material.delete()

        resp = self.client.get(tst_url)

        self.assertEqual(200, resp.status_code)
        self.assertFalse(bytes(name, 'utf-8') in resp.content)
        self.assertFalse(bytes(str(size), 'utf-8') in resp.content)
        self.assertFalse(bytes(details_url, 'utf-8') in resp.content)
        self.assertFalse(bytes(delete_url, 'utf-8') in resp.content)

    def test_material_form(self):
        tst_url = reverse('material_form')
        material_name = 'Material form test'
        material_size = 3.25

        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        # make sure, form is accessible
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 200)

        # make sure material did not existed before
        materials = models.Material.objects.filter(name=material_name, size_od=material_size)
        self.assertEqual(len(materials),
                         0,
                         msg='Material already exists - test can not be performed')

        # check if material can be created
        resp = self.client.post(tst_url,
                                dict(name=material_name, size_od=material_size),
                                follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('material_manager'))

        # chack if material was actually created
        materials = models.Material.objects.filter(name=material_name, size_od=material_size)
        self.assertEqual(len(materials), 1)

    def test_material_delete(self):
        # Create material
        material = models.Material.objects.create()
        tst_url = reverse('material_delete', kwargs={'pk': material.pk})
        self.assertTrue(self.client.login(email='known_user@somewhere.com', password='SomeSecretPassword'))

        # Should return error, since owner is not user
        resp = self.client.post(tst_url)
        self.assertEqual(resp.status_code, 404)
        # material should still be in database
        materials = models.Material.objects.filter(pk=material.pk)
        self.assertEqual(len(materials), 1)

        # get should return error, since there is only post endpoint
        resp = self.client.get(tst_url)
        self.assertEqual(resp.status_code, 404)
        # material should still be in database
        materials = models.Material.objects.filter(pk=material.pk)
        self.assertEqual(len(materials), 1)

        material.owner = self.user
        material.save()

        # Should redirect to material_manager and delete material
        resp = self.client.post(tst_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.redirect_chain) > 0)
        self.assertEqual(resp.redirect_chain[-1][0], reverse('material_manager'))
        # material should be deleted
        materials = models.Material.objects.filter(pk=material.pk)
        self.assertEqual(len(materials), 0)

        # Should return error, since material does not exist
        resp = self.client.post(tst_url)
        self.assertEqual(resp.status_code, 404)

