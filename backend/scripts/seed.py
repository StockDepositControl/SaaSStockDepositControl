import argparse
import asyncio
import os
import random
import sys
from datetime import timedelta, date
from decimal import Decimal
from faker import Faker

# Add project root to sys.path if not present
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.adapters.repositories.models import (
    Usuario, UserRole, Familia, Grupo, Marca, Articulo, StockPorDeposito, LotePorDeposito
)
from backend.adapters.database.connection import SQLAlchemyConnectionProvider
from backend.api.dependencies import get_password_hasher

async def run_seed(count: int, seed_val: int):
    fake = Faker('es_AR')
    if seed_val is not None:
        fake.seed_instance(seed_val)
        random.seed(seed_val)

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        db_user = os.getenv("DB_USER", "root")
        db_pass = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "stock_deposit_control")
        database_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        # Provide fallback to sqlite test DB for seamless tests if mysql is unavailable
        if not os.getenv("DB_HOST"):
            database_url = "sqlite+aiosqlite:///./test.db"

    provider = SQLAlchemyConnectionProvider(database_url=database_url)
    hasher = get_password_hasher()
    password_hash = hasher.hash("password123")

    tenants = ["GlobalMedica_01", "Farmanor_Branch_02"]
    roles = [UserRole.ADMINISTRADOR, UserRole.SUPERVISOR, UserRole.AUDITOR]
    sucursales = [1, 2]
    depositos = [1, 2, 3, 4, 5]

    async with provider.session() as session:
        # Clean existing table data to ensure idempotency
        from sqlalchemy import delete
        await session.raw_session.execute(delete(LotePorDeposito))
        await session.raw_session.execute(delete(StockPorDeposito))
        await session.raw_session.execute(delete(Articulo))
        await session.raw_session.execute(delete(Grupo))
        await session.raw_session.execute(delete(Familia))
        await session.raw_session.execute(delete(Marca))
        await session.raw_session.execute(delete(Usuario))
        await session.raw_session.flush()

        # Create Users
        usuarios = []
        for i in range(10):
            tenant = random.choice(tenants)
            sucursal = random.choice(sucursales)
            rol = random.choice(roles)
            unique_email = f"user_{i}_{random.randint(1000, 9999)}_{fake.email()}"
            usuarios.append(Usuario(
                tenant_id=tenant,
                nombre_completo=fake.name(),
                email=unique_email,
                password_hash=password_hash,
                is_active=True,
                rol=rol,
                id_sucursal=sucursal
            ))
        session.raw_session.add_all(usuarios)

        # Create Families
        familias = [
            Familia(des_familia="Medicamentos"),
            Familia(des_familia="Perfumería"),
            Familia(des_familia="Cosmética"),
            Familia(des_familia="Accesorios")
        ]
        session.raw_session.add_all(familias)
        await session.raw_session.flush()

        # Families Dictionary mapping
        med_fam_id = next(f.id_familia for f in familias if f.des_familia == "Medicamentos")
        taxable_fam_ids = [f.id_familia for f in familias if f.des_familia != "Medicamentos"]

        # Create Groups
        grupos = []
        for f in familias:
            for g_id in range(1, 4):
                grupos.append(Grupo(id_familia=f.id_familia, id_grupo=g_id, des_grupo=f"Grupo {g_id} de {f.des_familia}"))
        session.raw_session.add_all(grupos)

        # Create Brands
        marcas = [Marca(des_marca=fake.company()) for _ in range(10)]
        session.raw_session.add_all(marcas)
        await session.raw_session.flush()
        marca_ids = [m.id_marca for m in marcas]

        # Create Articles
        articulos = []
        # State C: 50% "Medicamentos", 50% Taxable
        half_count = count // 2
        for i in range(count):
            tenant = tenants[i % len(tenants)]
            is_med = i < half_count
            f_id = med_fam_id if is_med else random.choice(taxable_fam_ids)
            g_id = random.choice([1, 2, 3])
            
            # Use Decimal for monetary precision
            price_val = Decimal(str(round(random.uniform(10.0, 5000.0), 2)))

            art = Articulo(
                tenant_id=tenant,
                id_articulo=f"ART-{i:05d}",
                presentacion=fake.word(),
                des_articulo=f"Articulo {i}",
                id_marca=random.choice(marca_ids),
                id_familia=f_id,
                id_grupo=g_id,
                pcio_com_siva=price_val
            )
            articulos.append(art)
            
        session.raw_session.add_all(articulos)
        await session.raw_session.flush()

        # Create StockPorDeposito and LotePorDeposito
        stocks = []
        lotes = []
        
        # State A & B rules
        # State B: 25% expired lots
        total_lotes_planned = count
        expired_lotes_target = total_lotes_planned // 4

        lote_counter = 0

        for idx, art in enumerate(articulos):
            sucursal = random.choice(sucursales)
            deposito = random.choice(depositos)
            
            # Anomalous State A: Ghost Items (Theoretical > 0, Real == 0)
            is_ghost = random.random() < 0.1 # 10% chance
            
            stock_teorico = random.randint(10, 100)
            stock_real = 0 if is_ghost else stock_teorico

            stocks.append(StockPorDeposito(
                tenant_id=art.tenant_id,
                id_sucursal=sucursal,
                id_deposito=deposito,
                id_articulo=art.id_articulo,
                stock_real=stock_real,
                stock_teorico=stock_teorico,
                fue_auditado=False
            ))

            # Anomalous State B: Expired Lots
            is_expired = lote_counter < expired_lotes_target
            lote_counter += 1
            
            if is_expired:
                days_offset = -random.randint(1, 30) # Past 1-30 days
            else:
                days_offset = random.randint(1, 365) # Future 1-365 days
            
            vencimiento_date = fake.date_between(
                start_date=date.today() + timedelta(days=days_offset),
                end_date=date.today() + timedelta(days=days_offset)
            )

            lotes.append(LotePorDeposito(
                tenant_id=art.tenant_id,
                id_deposito=deposito,
                id_articulo=art.id_articulo,
                lote=f"LOT-{idx:05d}",
                vencimiento=vencimiento_date,
                stock_real=stock_real
            ))

        session.raw_session.add_all(stocks)
        session.raw_session.add_all(lotes)
        
        await session.commit()
        print(f"Successfully seeded {count} items. Created ghost items and {expired_lotes_target} expired lots.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database with test data.")
    parser.add_argument("--count", type=int, default=500, help="Number of articles to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for Faker determinism.")
    args = parser.parse_args()

    asyncio.run(run_seed(args.count, args.seed))
