import base64
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi import HTTPException
from pydantic import ValidationError
from app.routers.workshops import update_workshop
from app.schemas import WorkshopInput, WorkshopUpdateInput
from app.repositories.workshops import WorkshopRepository
from shared.db.models import Workshop


class WorkshopChangesTest(unittest.TestCase):
    def payload(self, **extra):
        return dict(name="Taller prueba", tax_id="ABC010203AB1", state="Puebla",
                    municipality="Puebla", colony="Centro", postal_code="72000", **extra)

    def test_create_locality_can_be_missing_null_or_blank(self):
        for extra in ({}, {"locality": None}, {"locality": "   "}):
            self.assertIsNone(WorkshopInput(**self.payload(**extra)).locality)

    def test_other_address_fields_still_required(self):
        data = self.payload()
        del data["colony"]
        with self.assertRaises(ValidationError):
            WorkshopInput(**data)

    def test_invalid_photo_rejected(self):
        with self.assertRaises(ValidationError):
            WorkshopUpdateInput(**self.payload(photo_data_url="data:image/png;base64,YWJj"))

    def repos(self, role="admin"):
        workshop = Workshop(id="w1", name="Original", is_active=True,
                            photo_data=b"previous", photo_content_type="image/png")
        repos = Mock()
        repos.workshops.get_any_membership.return_value = SimpleNamespace(role=SimpleNamespace(code=role), workshop=workshop)
        repos.workshops.find_by_name.return_value = None
        repos.workshops.find_by_tax_id.return_value = None
        repository = WorkshopRepository(None)
        repos.workshops.update_workshop.side_effect = repository.update_workshop
        repos.workshops.set_photo.side_effect = repository.set_photo
        return repos, workshop

    def test_admin_can_replace_photo_and_preserve_it_on_next_edit(self):
        repos, workshop = self.repos()
        image = b"\x89PNG\r\n\x1a\nphoto"
        photo = "data:image/png;base64," + base64.b64encode(image).decode()
        update_workshop("w1", WorkshopUpdateInput(**self.payload(photo_data_url=photo)), SimpleNamespace(id="u1"), repos)
        self.assertEqual(workshop.photo_data, image)
        repos.commit.assert_called_once()
        update_workshop("w1", WorkshopUpdateInput(**self.payload()), SimpleNamespace(id="u1"), repos)
        self.assertEqual(workshop.photo_data, image)

    def test_admin_in_other_workshop_cannot_edit_target(self):
        for role in ("reception", "technician", "customer"):
            repos, workshop = self.repos(role)
            with self.assertRaises(HTTPException) as error:
                update_workshop("w1", WorkshopUpdateInput(**self.payload()), SimpleNamespace(id="u1"), repos)
            self.assertEqual(error.exception.status_code, 403)
            repos.commit.assert_not_called()
            self.assertEqual(workshop.name, "Original")

    def test_missing_membership_cannot_edit(self):
        repos, _ = self.repos()
        repos.workshops.get_any_membership.return_value = None
        with self.assertRaises(HTTPException) as error:
            update_workshop("w1", WorkshopUpdateInput(**self.payload()), SimpleNamespace(id="u1"), repos)
        self.assertEqual(error.exception.status_code, 403)
        repos.commit.assert_not_called()
