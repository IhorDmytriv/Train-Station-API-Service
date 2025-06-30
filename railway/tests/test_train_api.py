import os
import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from railway.models import Train, TrainType
from railway.serializers import TrainListSerializer, TrainDetailSerializer

TRAIN_URL = reverse("railway:train-list")


def sample_train_type(**params):
    defaults = {
        "name": "Sample train type",
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)


def sample_train(**params):
    if "train_type" in params:
        train_type = params.pop("train_type")
    else:
        train_type = sample_train_type()

    defaults = {
        "name": "Sample train",
        "cargo_num": 5,
        "places_in_cargo": 20,
        "train_type": train_type,
    }
    defaults.update(params)
    return Train.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for recipe image upload"""
    return reverse("railway:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("railway:train-detail", args=[train_id])


class UnauthenticatedTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(TRAIN_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test",
            password="test_password"
        )
        self.client.force_login(self.user)
        self.train_type = sample_train_type(name="Train type")

    def test_list_trains_returns_all_trains(self):
        sample_train(name="Sample train 1", train_type=self.train_type)

        sample_train(name="Sample train 2", train_type=self.train_type)

        response = self.client.get(TRAIN_URL)
        trains = Train.objects.all()
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"], serializer.data)

    def test_list_trains_filtered_by_train_type(self):
        type_a = self.train_type
        type_b = sample_train_type(name="Type B")
        train1 = sample_train(name="A", train_type=type_a)
        sample_train(name="B", train_type=type_b)

        response = self.client.get(TRAIN_URL, {"train_type": f"{type_a.id}"})
        serializer = TrainListSerializer([train1], many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_list_trains_invalid_train_type_param(self):
        res = self.client.get(TRAIN_URL, {"train_type": "abc"})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_train_detail(self):
        train = sample_train(name="Train detail", train_type=self.train_type)

        url = detail_url(train.id)
        response = self.client.get(url)

        serializer = TrainDetailSerializer(train)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_train_forbidden(self):
        payload = {
            "name": "Sample train",
            "cargo_num": 5,
            "places_in_cargo": 20,
            "train_type": self.train_type.id,
        }

        response = self.client.post(TRAIN_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_train_not_allowed(self):
        train = sample_train(name="Train delete", train_type=self.train_type)

        url = detail_url(train.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin",
            password="test_password",
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.train_type = sample_train_type(name="Train type")

    def test_create_train(self):
        payload = {
            "name": "Sample train",
            "cargo_num": 5,
            "places_in_cargo": 20,
            "train_type": self.train_type.id,
        }

        response = self.client.post(TRAIN_URL, payload)

        train = Train.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(payload["name"], train.name)
        self.assertEqual(payload["cargo_num"], train.cargo_num)
        self.assertEqual(payload["places_in_cargo"], train.places_in_cargo)
        self.assertEqual(payload["train_type"], train.train_type.id)

    def test_delete_train_allowed(self):
        train = sample_train(name="Train delete", train_type=self.train_type)

        url = detail_url(train.id)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.admin",
            password="test_password",
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.train_type = sample_train_type(name="Train type")
        self.train = sample_train(
            name="Sample train", train_type=self.train_type
        )

    def tearDown(self):
        self.train.image.delete()

    def test_upload_image_to_train(self):
        """Test uploading an image to train"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(
                url,
                {"image": ntf},
                format="multipart"
            )
        self.train.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.train.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        response = self.client.post(
            url,
            {"image": "not image"},
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_train_list(self):
        url = TRAIN_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(
                url,
                {
                    "name": "Sample train with image",
                    "cargo_num": 5,
                    "places_in_cargo": 20,
                    "train_type": self.train_type.id,
                    "image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(name="Sample train with image")
        self.assertFalse(train.image)

    def test_image_url_is_shown_on_train_detail(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        response = self.client.get(detail_url(self.train.id))

        self.assertIn("image", response.data)

    def test_image_url_is_shown_on_train_list(self):
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        response = self.client.get(TRAIN_URL)

        self.assertIn("image", response.data["results"][0].keys())
