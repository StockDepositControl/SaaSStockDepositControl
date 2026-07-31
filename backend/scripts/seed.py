import argparse
import asyncio
import math
import os
import random
import sys
from datetime import timedelta, date, datetime
from decimal import Decimal
from faker import Faker
from dotenv import load_dotenv
load_dotenv()

# Add project root to sys.path if not present
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.adapters.repositories.models import (
    Familia, Grupo, Marca, Articulo, StockPorDeposito, LotePorDeposito, CodigoBarraArticulo,
    Role, User, UserRoleAssociation, RecordTenant, AuditRecord, DailyReport, CriticalShrinkageAlert, ActionType, RiskLevel
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
    database_url: str = None,
    url_articles: str = None,
    url_users: str = None,
    url_analytics: str = None,
):
    fake = Faker('es_AR')
    if seed_val is not None:
        fake.seed_instance(seed_val)
        random.seed(seed_val)

    if url_articles and url_users and url_analytics:
        pass
    elif not database_url:
        db_user = os.getenv("DB_USER", "root")
        db_pass = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        url_articles = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{os.getenv('DB_NAME_ARTICLES', 'db_articles')}"
        url_users = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{os.getenv('DB_NAME_USERS', 'db_users')}"
        url_analytics = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{os.getenv('DB_NAME_ANALYTICS', 'db_analytics')}"
    else:
        if "sqlite" in database_url:
            if "test_articles" in database_url or "test_users" in database_url or "test_analytics" in database_url:
                url_articles = database_url
                url_users = database_url
                url_analytics = database_url
            else:
                url_articles = database_url.replace("testdb", "test_articles").replace(":memory:", "file:mem_articles?mode=memory&cache=shared&uri=true")
                url_users = database_url.replace("testdb", "test_users").replace(":memory:", "file:mem_users?mode=memory&cache=shared&uri=true")
                url_analytics = database_url.replace("testdb", "test_analytics").replace(":memory:", "file:mem_analytics?mode=memory&cache=shared&uri=true")
        else:
            url_articles = url_users = url_analytics = database_url

    provider_articles = SQLAlchemyConnectionProvider(database_url=url_articles)
    provider_users = SQLAlchemyConnectionProvider(database_url=url_users)
    provider_analytics = SQLAlchemyConnectionProvider(database_url=url_analytics)
    hasher = BcryptPasswordHasher()
    password_hash = hasher.hash("password123")

    sucursales = [1, 2]
    depositos = list(range(1, num_deposits + 1))

    try:
        # Ensure tables exist (e.g. for in-memory SQLite or fresh DB)
        async with provider_articles.engine.begin() as conn:
            from backend.adapters.repositories.models import BaseArticles
            await conn.run_sync(BaseArticles.metadata.create_all)
        async with provider_users.engine.begin() as conn:
            from backend.adapters.repositories.models import BaseUsers
            await conn.run_sync(BaseUsers.metadata.create_all)
        async with provider_analytics.engine.begin() as conn:
            from backend.adapters.repositories.models import BaseAnalytics
            await conn.run_sync(BaseAnalytics.metadata.create_all)

        async with provider_articles.session() as s_articles, \
                   provider_users.session() as s_users, \
                   provider_analytics.session() as s_analytics:
            # 1. Clean existing table data safely (Idempotency)
            from sqlalchemy import delete
            await s_analytics.raw_session.execute(delete(CriticalShrinkageAlert))
            await s_analytics.raw_session.execute(delete(DailyReport))
            await s_analytics.raw_session.execute(delete(AuditRecord))
            await s_analytics.raw_session.execute(delete(RecordTenant))
            await s_users.raw_session.execute(delete(UserRoleAssociation))
            await s_users.raw_session.execute(delete(User))
            await s_users.raw_session.execute(delete(Role))
            await s_articles.raw_session.execute(delete(CodigoBarraArticulo))
            await s_articles.raw_session.execute(delete(LotePorDeposito))
            await s_articles.raw_session.execute(delete(StockPorDeposito))
            await s_articles.raw_session.execute(delete(Articulo))
            await s_articles.raw_session.execute(delete(Grupo))
            await s_articles.raw_session.execute(delete(Familia))
            await s_articles.raw_session.execute(delete(Marca))
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 2. Seed Families (State C Fiscal Mix requirement: Medicamentos 0% VAT, others taxable)
            familias = [
                Familia(id_familia="01", des_familia="Medicamentos"),
                Familia(id_familia="02", des_familia="Perfumería"),
                Familia(id_familia="03", des_familia="Cosmética"),
                Familia(id_familia="04", des_familia="Accesorios")
            ]
            s_articles.raw_session.add_all(familias)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            med_fam_id = "01"
            taxable_fam_ids = ["02", "03", "04"]

            # 3. Seed Groups (3 per family)
            grupos = []
            for f in familias:
                for g_idx in range(1, 4):
                    g_id = f"{g_idx:02d}"
                    grupos.append(Grupo(id_familia=f.id_familia, id_grupo=g_id, des_grupo=f"Grupo {g_id} - {f.des_familia}"[:40]))
            s_articles.raw_session.add_all(grupos)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 4. Seed Brands (Laboratories)
            marcas = [Marca(des_marca=f"Laboratorio {fake.company()}"[:80]) for _ in range(15)]
            s_articles.raw_session.add_all(marcas)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()
            marca_ids = [m.id_marca for m in marcas]

            # 5. Seed Articles (State C: 50% Medicamentos exempt, 50% Taxable)
            articulos = []
            half_count = count // 2
            for i in range(count):
                is_med = i < half_count
                f_id = med_fam_id if is_med else random.choice(taxable_fam_ids)
                g_id = f"{random.randint(1, 3):02d}"
                price_val = round(random.uniform(150.0, 12500.0), 2)

                prefix = "MED" if is_med else "ART"
                des_art = f"{prefix} {fake.word().capitalize()} {random.randint(10, 1000)}mg"[:255]

                art = Articulo(
                    id_articulo=f"ART-{i:05d}".ljust(25),
                    presentacion=f"Caja x {random.choice([10, 20, 30, 60])} comp"[:255],
                    des_articulo=des_art,
                    id_marca=random.choice(marca_ids),
                    id_familia=f_id,
                    id_grupo=g_id,
                    pcio_com_siva=price_val
                )
                articulos.append(art)
            s_articles.raw_session.add_all(articulos)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 6. Seed StockPorDeposito, LotePorDeposito, and CodigoBarraArticulo
            stocks = []
            lotes = []
            barcodes = []

            ghost_count_target = math.ceil(count * ghost_rate)
            ghost_indices = set(random.sample(range(count), ghost_count_target))

            for idx, art in enumerate(articulos):
                empresa = 1 if (idx % 2 == 0) else 2
                sucursal = random.choice(sucursales)
                deposito = random.choice(depositos)
                is_ghost = idx in ghost_indices

                stock_real = 0.0 if is_ghost else float(random.randint(10, 200))

                stocks.append(StockPorDeposito(
                    id_empresa=empresa,
                    id_sucursal=sucursal,
                    id_deposito=deposito,
                    id_articulo=art.id_articulo,
                    stock_real=stock_real
                ))

                barcodes.append(CodigoBarraArticulo(
                    id_articulo=art.id_articulo,
                    cod_barra=f"779{idx:08d}01"
                ))

                num_lotes = random.randint(1, 3)
                for l_idx in range(num_lotes):
                    rand_val = random.random()
                    if rand_val < expired_rate:
                        days_offset = -random.randint(1, 180)
                    elif rand_val < expired_rate + 0.15:
                        days_offset = random.randint(1, 30)
                    elif rand_val < expired_rate + 0.25:
                        days_offset = random.randint(31, 60)
                    else:
                        days_offset = random.randint(61, 365)

                    vencimiento_date = date.today() + timedelta(days=days_offset)
                    lote_stock = max(0.0, float(stock_real // num_lotes))

                    lotes.append(LotePorDeposito(
                        id_empresa=empresa,
                        id_sucursal=sucursal,
                        id_deposito=deposito,
                        id_articulo=art.id_articulo,
                        lote=f"L{idx:04d}{l_idx+1}"[:10],
                        vencimiento=vencimiento_date.strftime("%Y-%m-%d"),
                        stock_real=lote_stock
                    ))

            s_articles.raw_session.add_all(stocks)
            s_articles.raw_session.add_all(barcodes)
            s_articles.raw_session.add_all(lotes)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 7. Seed Roles (db_users)
            role_admin = Role(name="ADMINISTRATOR", description="Full system access and global configuration")
            role_sup = Role(name="SUPERVISOR", description="Branch-level management and audit validation permissions")
            role_aud = Role(name="AUDITOR", description="Field auditing, counting, and scan execution permissions")
            s_users.raw_session.add_all([role_admin, role_sup, role_aud])
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 8. Seed Users & UserRoles (db_users)
            new_users = []
            for idx in range(12):
                sucursal = sucursales[idx % len(sucursales)]
                first, *last = fake.name().split()
                last_name = " ".join(last) if last else "Doe"
                new_u = User(
                    first_name=first,
                    last_name=last_name,
                    email=f"user_{idx}@example.com",
                    password_hash=password_hash,
                    branch_id=sucursal,
                    is_active=True
                )
                new_users.append(new_u)
            s_users.raw_session.add_all(new_users)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            user_role_assocs = []
            for u in new_users:
                role_obj = random.choice([role_admin, role_sup, role_aud])
                user_role_assocs.append(UserRoleAssociation(user_id=u.user_id, role_id=role_obj.role_id))
            s_users.raw_session.add_all(user_role_assocs)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 9. Seed RecordTenants (db_analytics)
            rec_tenants = [
                RecordTenant(tenant_name="GlobalMedica Inc.", pharmacy_code="FARMA-001"),
                RecordTenant(tenant_name="Farmanor Branch 2", pharmacy_code="FARMA-002")
            ]
            s_analytics.raw_session.add_all(rec_tenants)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 10. Seed AuditRecords (db_analytics)
            analytics_audits = []
            actions = [ActionType.ADDITION, ActionType.REMOVAL, ActionType.NO_ACTION]
            audit_sample = random.sample(articulos, min(200, len(articulos)))
            for art in audit_sample:
                t_obj = random.choice(rec_tenants)
                act_type = random.choice(actions)
                cant = 0 if act_type == ActionType.NO_ACTION else random.randint(1, 20)
                applied_vat = Decimal('0.0000') if art.id_familia == med_fam_id else Decimal(str(vat_rate))
                unit_cost = Decimal(str(art.pcio_com_siva))
                val_amount = (unit_cost * (Decimal('1') + applied_vat) * Decimal(str(cant))).quantize(Decimal('0.0001'))

                analytics_audits.append(AuditRecord(
                    tenant_id=t_obj.tenant_id,
                    warehouse_id=random.choice(depositos),
                    article_code=art.id_articulo.strip(),
                    user_id=random.choice(new_users).user_id,
                    action_type=act_type,
                    affected_amount=cant,
                    applied_unit_cost=unit_cost,
                    applied_vat_rate=applied_vat,
                    valorized_amount=val_amount,
                    scan_timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                ))
            s_analytics.raw_session.add_all(analytics_audits)

            # 11. Seed DailyReports (db_analytics)
            daily_reports = []
            for t_obj in rec_tenants:
                daily_reports.append(DailyReport(
                    tenant_id=t_obj.tenant_id,
                    report_date=date.today() - timedelta(days=1),
                    total_audit_articles=len(articulos) // 2,
                    total_addition_amount=150,
                    total_shrinkage_amount=30,
                    total_addition_value=Decimal('25000.5000'),
                    total_shrinkage_value=Decimal('4200.0000')
                ))
            s_analytics.raw_session.add_all(daily_reports)

            # 12. Seed CriticalShrinkageAlerts (db_analytics)
            critical_alerts = []
            for lot in lotes:
                lot_venc_date = datetime.strptime(lot.vencimiento, "%Y-%m-%d").date()
                if lot_venc_date < date.today() + timedelta(days=30):
                    t_obj = random.choice(rec_tenants)
                    days_to_exp = (lot_venc_date - date.today()).days
                    risk = RiskLevel.RED if days_to_exp <= 0 else (RiskLevel.YELLOW if days_to_exp <= 30 else RiskLevel.GREEN)
                    art_ref = next((a for a in articulos if a.id_articulo == lot.id_articulo), articulos[0])
                    amt_at_risk = Decimal(str(lot.stock_real)) * Decimal(str(art_ref.pcio_com_siva))

                    critical_alerts.append(CriticalShrinkageAlert(
                        tenant_id=t_obj.tenant_id,
                        warehouse_id=lot.id_deposito,
                        article_code=lot.id_articulo.strip(),
                        batch_number=lot.lote,
                        expiration_date=lot_venc_date,
                        days_to_expiration=days_to_exp,
                        risk_level=risk,
                        stock_at_risk=int(lot.stock_real),
                        amount_at_risk=amt_at_risk.quantize(Decimal('0.0001'))
                    ))
            s_analytics.raw_session.add_all(critical_alerts)

            await s_articles.commit(); await s_users.commit(); await s_analytics.commit()

            today_str = date.today().strftime("%Y-%m-%d")
            expired_count = sum(1 for l in lotes if l.vencimiento < today_str)
            print(f"✅ Seeding Complete!")
            print(f"   • Articles: {len(articulos)} (Medicamentos: {half_count}, Taxable: {count - half_count})")
            print(f"   • Stock rows: {len(stocks)} (Ghost Items: {ghost_count_target})")
            print(f"   • Barcodes: {len(barcodes)}")
            print(f"   • Lots: {len(lotes)} (Expired: {expired_count})")
            print(f"   • Roles (db_users): 3")
            print(f"   • Users (db_users): {len(new_users)}")
            print(f"   • Record Tenants (db_analytics): {len(rec_tenants)}")
            print(f"   • Analytics Audits (db_analytics): {len(analytics_audits)}")
            print(f"   • Daily Reports (db_analytics): {len(daily_reports)}")
            print(f"   • Critical Alerts (db_analytics): {len(critical_alerts)}")
    finally:
        await provider_articles.engine.dispose(); await provider_users.engine.dispose(); await provider_analytics.engine.dispose()

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
