import argparse
import asyncio
import math
import os
import random
import sys
from datetime import timedelta, date, datetime
from decimal import Decimal
from faker import Faker

# Add project root to sys.path if not present
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.adapters.repositories.models import (
    Usuario, UserRole, Familia, Grupo, Marca, Articulo, StockPorDeposito, LotePorDeposito, AuditoriaRegistro, TipoAccion
)
from backend.adapters.database.connection import SQLAlchemyConnectionProvider
from backend.adapters.security.password_hasher import BcryptPasswordHasher

async def run_seed(
    count: int = 500,
    seed_val: int = 42,
    num_deposits: int = 5,
    ghost_rate: float = 0.10,
    expired_rate: float = 0.25,
    vat_rate: float = 0.21,
    database_url: str = None
):
    fake = Faker('es_AR')
    if seed_val is not None:
        fake.seed_instance(seed_val)
        random.seed(seed_val)

    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            db_user = os.getenv("DB_USER", "root")
            db_pass = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "3306")
            db_name = os.getenv("DB_NAME", "stock_deposit_control")
            database_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            if not os.getenv("DB_HOST"):
                database_url = "sqlite+aiosqlite:///./test.db"

    provider = SQLAlchemyConnectionProvider(database_url=database_url)
    hasher = BcryptPasswordHasher()
    password_hash = hasher.hash("password123")

    tenants = ["GlobalMedica_01", "Farmanor_Branch_02"]
    roles = [UserRole.ADMINISTRADOR, UserRole.SUPERVISOR, UserRole.AUDITOR]
    sucursales = [1, 2]
    depositos = list(range(1, num_deposits + 1))

    # Ensure tables exist (e.g. for in-memory SQLite or fresh DB)
    async with provider.engine.begin() as conn:
        from backend.adapters.repositories.models import Base
        await conn.run_sync(Base.metadata.create_all)

    async with provider.session() as session:
        # 1. Clean existing table data safely (Idempotency)

        from sqlalchemy import delete
        await session.raw_session.execute(delete(AuditoriaRegistro))
        await session.raw_session.execute(delete(LotePorDeposito))
        await session.raw_session.execute(delete(StockPorDeposito))
        await session.raw_session.execute(delete(Articulo))
        await session.raw_session.execute(delete(Grupo))
        await session.raw_session.execute(delete(Familia))
        await session.raw_session.execute(delete(Marca))
        await session.raw_session.execute(delete(Usuario))
        await session.raw_session.flush()

        # 2. Seed Users (6 per tenant)
        usuarios = []
        for tenant in tenants:
            for idx in range(6):
                sucursal = sucursales[idx % len(sucursales)]
                rol = roles[idx % len(roles)]
                email = f"{rol.value}_{idx}_{tenant.lower()}@example.com"
                usuarios.append(Usuario(
                    tenant_id=tenant,
                    nombre_completo=fake.name(),
                    email=email,
                    password_hash=password_hash,
                    is_active=True,
                    rol=rol,
                    id_sucursal=sucursal
                ))
        session.raw_session.add_all(usuarios)
        await session.raw_session.flush()

        # 3. Seed Families (State C Fiscal Mix requirement: Medicamentos 0% VAT, others taxable)
        familias = [
            Familia(des_familia="Medicamentos"),
            Familia(des_familia="Perfumería"),
            Familia(des_familia="Cosmética"),
            Familia(des_familia="Accesorios")
        ]
        session.raw_session.add_all(familias)
        await session.raw_session.flush()

        med_fam_id = next(f.id_familia for f in familias if f.des_familia == "Medicamentos")
        taxable_fam_ids = [f.id_familia for f in familias if f.des_familia != "Medicamentos"]

        # 4. Seed Groups (3 per family)
        grupos = []
        for f in familias:
            for g_id in range(1, 4):
                grupos.append(Grupo(id_familia=f.id_familia, id_grupo=g_id, des_grupo=f"Grupo {g_id} - {f.des_familia}"))
        session.raw_session.add_all(grupos)

        # 5. Seed Brands (Laboratories)
        marcas = [Marca(des_marca=f"Laboratorio {fake.company()}") for _ in range(15)]
        session.raw_session.add_all(marcas)
        await session.raw_session.flush()
        marca_ids = [m.id_marca for m in marcas]

        # 6. Seed Articles (State C: 50% Medicamentos exempt, 50% Taxable)
        articulos = []
        half_count = count // 2
        for i in range(count):
            tenant = tenants[i % len(tenants)]
            is_med = i < half_count
            f_id = med_fam_id if is_med else random.choice(taxable_fam_ids)
            g_id = random.choice([1, 2, 3])
            price_val = Decimal(str(round(random.uniform(150.0, 12500.0), 2)))

            prefix = "MED" if is_med else "ART"
            des_art = f"{prefix} {fake.word().capitalize()} {random.randint(10, 1000)}mg"
            
            art = Articulo(
                tenant_id=tenant,
                id_articulo=f"ART-{i:05d}",
                presentacion=f"Caja x {random.choice([10, 20, 30, 60])} comp",
                des_articulo=des_art,
                id_marca=random.choice(marca_ids),
                id_familia=f_id,
                id_grupo=g_id,
                pcio_com_siva=price_val
            )
            articulos.append(art)
        session.raw_session.add_all(articulos)
        await session.raw_session.flush()

        # 7. Seed StockPorDeposito & LotePorDeposito
        stocks = []
        lotes = []

        # State A: Ghost Items allocation (theoretical > 0, real == 0)
        ghost_count_target = math.ceil(count * ghost_rate)
        ghost_indices = set(random.sample(range(count), ghost_count_target))

        for idx, art in enumerate(articulos):
            sucursal = random.choice(sucursales)
            deposito = random.choice(depositos)
            is_ghost = idx in ghost_indices

            stock_teorico = random.randint(15, 200)
            stock_real = 0 if is_ghost else (stock_teorico if random.random() > 0.3 else stock_teorico + random.randint(-10, 10))

            stocks.append(StockPorDeposito(
                tenant_id=art.tenant_id,
                id_sucursal=sucursal,
                id_deposito=deposito,
                id_articulo=art.id_articulo,
                stock_real=stock_real,
                stock_teorico=stock_teorico,
                fue_auditado=random.choice([True, False])
            ))

            # State B: Expired lot clusters & FEFO tiers
            num_lotes = random.randint(1, 3)
            for l_idx in range(num_lotes):
                rand_val = random.random()
                if rand_val < expired_rate:
                    # Expired: past 1 to 180 days
                    days_offset = -random.randint(1, 180)
                elif rand_val < expired_rate + 0.15:
                    # Critical tier FEFO: 1 to 30 days remaining
                    days_offset = random.randint(1, 30)
                elif rand_val < expired_rate + 0.25:
                    # Warning tier FEFO: 31 to 60 days remaining
                    days_offset = random.randint(31, 60)
                else:
                    # Normal shelf life: 61 to 365 days
                    days_offset = random.randint(61, 365)

                vencimiento_date = date.today() + timedelta(days=days_offset)
                lote_stock = max(0, stock_real // num_lotes)

                lotes.append(LotePorDeposito(
                    tenant_id=art.tenant_id,
                    id_deposito=deposito,
                    id_articulo=art.id_articulo,
                    lote=f"LOT-{idx:05d}-{l_idx+1}",
                    vencimiento=vencimiento_date,
                    stock_real=lote_stock
                ))

        session.raw_session.add_all(stocks)
        session.raw_session.add_all(lotes)
        await session.raw_session.flush()

        # 8. Seed AuditoriaRegistro (Movements Ledger for US 6 reporting validation)
        auditorias = []
        user_by_tenant = {t: [u for u in usuarios if u.tenant_id == t] for t in tenants}

        # Select a sample of 200 articles to create audit movement history
        audit_sample = random.sample(articulos, min(200, len(articulos)))
        for art in audit_sample:
            user = random.choice(user_by_tenant[art.tenant_id])
            tipo = random.choice([TipoAccion.ALTA, TipoAccion.BAJA, TipoAccion.SIN_ACCION])
            cant = 0 if tipo == TipoAccion.SIN_ACCION else random.randint(1, 20)

            # Fiscal calculation: Medicamentos (id_familia == med_fam_id) = 0% VAT, others apply vat_rate
            if art.id_familia == med_fam_id:
                unit_cost = art.pcio_com_siva
            else:
                unit_cost = art.pcio_com_siva * Decimal(str(1 + vat_rate))

            monto_valorizado = (unit_cost * cant).quantize(Decimal('0.0001'))

            auditorias.append(AuditoriaRegistro(
                tenant_id=art.tenant_id,
                id_sucursal=user.id_sucursal,
                id_deposito=random.choice(depositos),
                id_articulo=art.id_articulo,
                tipo_accion=tipo.value,
                cantidad_afectada=cant,
                monto_valorizado=monto_valorizado,
                id_usuario=user.id_usuario,
                fecha_hora=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            ))


        session.raw_session.add_all(auditorias)
        await session.commit()

        expired_count = sum(1 for l in lotes if l.vencimiento < date.today())
        print(f"✅ Seeding Complete!")
        print(f"   • Articles: {len(articulos)} (Medicamentos: {half_count}, Taxable: {count - half_count})")
        print(f"   • Stock rows: {len(stocks)} (Ghost Items: {ghost_count_target})")
        print(f"   • Lots: {len(lotes)} (Expired: {expired_count})")
        print(f"   • Audit entries: {len(auditorias)}")
        print(f"   • Users: {len(usuarios)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parametric Database Seeding Script.")
    parser.add_argument("--count", type=int, default=500, help="Total articles to generate.")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility.")
    parser.add_argument("--deposits", type=int, default=5, help="Number of virtual deposits.")
    parser.add_argument("--ghost-rate", type=float, default=0.10, help="Fraction of Ghost items.")
    parser.add_argument("--expired-rate", type=float, default=0.25, help="Fraction of expired lots.")
    parser.add_argument("--vat-rate", type=float, default=0.21, help="Default VAT rate for taxable items.")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL override.")
    args = parser.parse_args()

    asyncio.run(run_seed(
        count=args.count,
        seed_val=args.seed,
        num_deposits=args.deposits,
        ghost_rate=args.ghost_rate,
        expired_rate=args.expired_rate,
        vat_rate=args.vat_rate,
        database_url=args.db_url
    ))
