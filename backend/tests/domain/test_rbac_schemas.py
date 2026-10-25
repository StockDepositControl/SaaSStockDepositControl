from decimal import Decimal

from backend.app.articles.models import ArticuloAdminOut, ArticuloPublicOut


def test_articulo_public_out_strips_sensitive_field():
    """
    Ensure the public schema structurally excludes the pcio_com_siva field.
    """
    data = {
        "tenant_id": "tenant-1",
        "id_articulo": "ART-001",
        "presentacion": "Box of 20",
        "des_articulo": "Paracetamol",
        "pcio_com_siva": Decimal("120.50"),
    }

    public_out = ArticuloPublicOut(**data)

    # Assert sensitive field is omitted and not present in dump
    assert hasattr(public_out, "des_articulo")
    assert not hasattr(public_out, "pcio_com_siva")
    assert "pcio_com_siva" not in public_out.model_dump()


def test_articulo_admin_out_includes_sensitive_field():
    """
    Ensure the admin schema structurally includes the pcio_com_siva field.
    """
    data = {
        "tenant_id": "tenant-1",
        "id_articulo": "ART-001",
        "presentacion": "Box of 20",
        "des_articulo": "Paracetamol",
        "pcio_com_siva": Decimal("120.50"),
    }

    admin_out = ArticuloAdminOut(**data)

    # Assert sensitive field is retained and present in dump
    assert hasattr(admin_out, "pcio_com_siva")
    assert admin_out.pcio_com_siva == Decimal("120.50")
    assert "pcio_com_siva" in admin_out.model_dump()
