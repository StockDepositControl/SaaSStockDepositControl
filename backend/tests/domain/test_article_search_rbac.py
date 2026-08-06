import pytest
from decimal import Decimal

from backend.app.articles.models import Articulo, ArticuloPublicOut, ArticuloAdminOut

@pytest.fixture
def sample_domain_article():
    return Articulo(
        id_articulo="ART-500",
        presentacion="Caja x 30 comprimidos",
        des_articulo="Paracetamol 500mg",
        id_marca=1,
        des_marca="Genfar",
        id_familia="01",
        des_familia="Medicamentos",
        id_grupo="02",
        des_grupo="Analgésicos",
        pcio_com_siva=Decimal("250.75")
    )

def test_public_out_list_serialization_masks_cost(sample_domain_article):
    """
    Ensure ArticuloPublicOut serialization for search results returned to auditors/supervisors
    completely excludes the sensitive purchase cost field (pcio_com_siva).
    """
    results = [sample_domain_article]
    public_outs = [ArticuloPublicOut.model_validate(art) for art in results]

    assert len(public_outs) == 1
    out = public_outs[0]

    assert out.id_articulo == "ART-500"
    assert out.des_articulo == "Paracetamol 500mg"
    assert out.des_marca == "Genfar"
    assert not hasattr(out, "pcio_com_siva")

    dump = out.model_dump()
    assert "pcio_com_siva" not in dump

def test_admin_out_list_serialization_retains_cost(sample_domain_article):
    """
    Ensure ArticuloAdminOut serialization for search results returned to administrators
    includes the sensitive purchase cost field (pcio_com_siva).
    """
    results = [sample_domain_article]
    admin_outs = [ArticuloAdminOut.model_validate(art) for art in results]

    assert len(admin_outs) == 1
    out = admin_outs[0]

    assert out.id_articulo == "ART-500"
    assert hasattr(out, "pcio_com_siva")
    assert out.pcio_com_siva == Decimal("250.75")

    dump = out.model_dump()
    assert "pcio_com_siva" in dump
    assert dump["pcio_com_siva"] == Decimal("250.75")
