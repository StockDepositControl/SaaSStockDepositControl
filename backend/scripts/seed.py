import argparse
import asyncio
import math
import os
import random
import sys
import uuid
from datetime import timedelta, date, datetime
from decimal import Decimal
from faker import Faker
from dotenv import load_dotenv
load_dotenv()

# Add project root to sys.path if not present
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.adapters.repositories.models import (
    Familia, Grupo, Marca, Articulo, StockPorDeposito, LotePorDeposito, CodigoBarraArticulo,
    Empresa, Sucursal, Deposito,
    Enterprise, Branch, Role, User, UserRoleAssociation,
    RecordTenant, AuditRecord, DailyReport, CriticalShrinkageAlert, WorkSession, ActionType, RiskLevel, SessionStatus
)
from backend.adapters.database.connection import SQLAlchemyConnectionProvider, resolve_database_url
from backend.adapters.security.password_hasher import BcryptPasswordHasher

def resolve_seed_urls(
    database_url: str = None,
    url_articles: str = None,
    url_users: str = None,
    url_analytics: str = None,
) -> tuple[str, str, str]:
    """
    URLs for (articles, users, analytics): explicit per-database URLs win, then a
    single ``database_url`` override, then the same env precedence as the app and
    Alembic (``resolve_database_url``).
    """
    if url_articles and url_users and url_analytics:
        return url_articles, url_users, url_analytics
    if not database_url:
        return (
            resolve_database_url("articles"),
            resolve_database_url("users"),
            resolve_database_url("analytics"),
        )
    if "sqlite" not in database_url:
        return database_url, database_url, database_url
    if any(name in database_url for name in ("test_articles", "test_users", "test_analytics")):
        return database_url, database_url, database_url
    return (
        database_url.replace("testdb", "test_articles").replace(":memory:", "file:mem_articles?mode=memory&cache=shared&uri=true"),
        database_url.replace("testdb", "test_users").replace(":memory:", "file:mem_users?mode=memory&cache=shared&uri=true"),
        database_url.replace("testdb", "test_analytics").replace(":memory:", "file:mem_analytics?mode=memory&cache=shared&uri=true"),
    )


async def run_seed(
    count: int = 500,
    seed_val: int = 42,
    num_deposits: int = 1,
    ghost_rate: float = 0.10,
    expired_rate: float = 0.25,
    vat_rate: float = 0.21,
    shrinkage_rate: float = 0.0,
    goods_received_rate: float = 0.0,
    database_url: str = None,
    url_articles: str = None,
    url_users: str = None,
    url_analytics: str = None,
):
    fake = Faker('es_AR')
    if seed_val is not None:
        fake.seed_instance(seed_val)
        random.seed(seed_val)

    url_articles, url_users, url_analytics = resolve_seed_urls(
        database_url, url_articles, url_users, url_analytics
    )

    provider_articles = SQLAlchemyConnectionProvider(database_url=url_articles)
    provider_users = SQLAlchemyConnectionProvider(database_url=url_users)
    provider_analytics = SQLAlchemyConnectionProvider(database_url=url_analytics)
    hasher = BcryptPasswordHasher()
    password_hash = hasher.hash("123456")

    sucursales_ids = [1]
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
            await s_analytics.raw_session.execute(delete(WorkSession))
            await s_analytics.raw_session.execute(delete(RecordTenant))
            await s_users.raw_session.execute(delete(UserRoleAssociation))
            await s_users.raw_session.execute(delete(User))
            await s_users.raw_session.execute(delete(Role))
            await s_users.raw_session.execute(delete(Branch))
            await s_users.raw_session.execute(delete(Enterprise))
            await s_articles.raw_session.execute(delete(CodigoBarraArticulo))
            await s_articles.raw_session.execute(delete(LotePorDeposito))
            await s_articles.raw_session.execute(delete(StockPorDeposito))
            await s_articles.raw_session.execute(delete(Articulo))
            await s_articles.raw_session.execute(delete(Grupo))
            await s_articles.raw_session.execute(delete(Familia))
            await s_articles.raw_session.execute(delete(Marca))
            await s_articles.raw_session.execute(delete(Deposito))
            await s_articles.raw_session.execute(delete(Sucursal))
            await s_articles.raw_session.execute(delete(Empresa))
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 1.5. Seed Empresa, Sucursales, and Depositos (db_articles)
            empresa_obj = Empresa(id_empresa=1, des_empresa="Empresa Principal")
            s_articles.raw_session.add(empresa_obj)

            sucursales_objs = [
                Sucursal(id_sucursal=1, id_empresa=1, des_sucursal="Sucursal Central")
            ]
            s_articles.raw_session.add_all(sucursales_objs)

            depositos_objs = []
            valid_deposito_pairs = []
            for d_id in range(1, num_deposits + 1):
                # Distribute deposits across sucursales
                s_id = sucursales_ids[(d_id - 1) % len(sucursales_ids)]
                depositos_objs.append(Deposito(
                    id_sucursal=s_id,
                    id_deposito=d_id,
                    id_empresa=1,
                    des_deposito=f"Deposito {d_id}"[:30]
                ))
                valid_deposito_pairs.append((s_id, d_id))
            s_articles.raw_session.add_all(depositos_objs)

            # 1.6. Seed Enterprise and Branch (db_users)
            enterprise_user = Enterprise(tenant_id=1, description="Empresa Principal")
            s_users.raw_session.add(enterprise_user)
            await s_users.raw_session.flush()

            branch_user = Branch(id_branch=1, tenant_id=1, description="Sucursal Central")
            s_users.raw_session.add(branch_user)
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
                price_val = Decimal(str(round(random.uniform(150.0, 12500.0), 2)))

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
                empresa = 1
                sucursal, deposito = random.choice(valid_deposito_pairs)
                is_ghost = idx in ghost_indices

                stock_real = 0 if is_ghost else random.randint(10, 200)

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
                    lote_stock = max(0, int(stock_real // num_lotes))

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
            role_admin = Role(name="administrador", description="Acceso total al sistema y configuración global")
            role_sup = Role(name="supervisor", description="Gestión a nivel de sucursal y validación de auditorías")
            role_aud = Role(name="auditor", description="Ejecución de auditoría, conteo y escaneo en campo")
            s_users.raw_session.add_all([role_admin, role_sup, role_aud])
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 8. Seed Users & UserRoles (db_users)
            new_users = []
            user_role_assocs = []

            # Deterministic core accounts for Tenant 1
            deterministic_profiles = [
                ("Admin", "Global", "admin@globalmedica.com", role_admin, True),
                ("Supervisor", "Centro", "supervisor@globalmedica.com", role_sup, True),
                ("Auditor", "Campo", "auditor@globalmedica.com", role_aud, True),
            ]
            for first, last, email_addr, role_obj, active_flag in deterministic_profiles:
                u_obj = User(
                    tenant_id=1,
                    first_name=first,
                    last_name=last,
                    email=email_addr,
                    password_hash=password_hash,
                    branch_id=1,
                    is_active=active_flag
                )
                new_users.append(u_obj)
                # Stash role for association after flush provides user_id
                u_obj._target_role = role_obj

            s_users.raw_session.add_all(new_users)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            for u in new_users:
                user_role_assocs.append(UserRoleAssociation(user_id=u.user_id, role_id=u._target_role.role_id))
            s_users.raw_session.add_all(user_role_assocs)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 9. Seed RecordTenants (db_analytics)
            rec_tenants = [
                RecordTenant(tenant_id=1, tenant_name="GlobalMedica Inc.", pharmacy_code="FARMA-001")
            ]
            s_analytics.raw_session.add_all(rec_tenants)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 9.5. Seed WorkSessions (db_analytics)
            work_sessions = []
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_end = datetime.combine(date.today(), datetime.max.time())
            for t_obj in rec_tenants:
                work_sessions.append(WorkSession(
                    tenant_id=t_obj.tenant_id,
                    branch_id=1,
                    opened_at=today_start,
                    closed_at=today_end,
                    status=SessionStatus.OPEN.value
                ))
            s_analytics.raw_session.add_all(work_sessions)
            await s_articles.raw_session.flush(); await s_users.raw_session.flush(); await s_analytics.raw_session.flush()

            # 10. Seed AuditRecords (db_analytics)
            analytics_audits = []
            if shrinkage_rate > 0 and len(work_sessions) > 0:
                ws_id = work_sessions[0].session_id
                shrink_count = math.ceil(count * shrinkage_rate)
                shrink_articles = random.sample(articulos, min(shrink_count, len(articulos)))
                shrinkage_reasons = [
                    "Rotura de envase",
                    "Producto vencido",
                    "Deterioro por humedad",
                    "Diferencia de inventario / Merma",
                    "Robo / Hurto identificado",
                    "Devolución a proveedor por falla"
                ]
                for art in shrink_articles:
                    affected = random.randint(1, 5)
                    unit_cost = art.pcio_com_siva or Decimal("100.00")
                    is_med = (art.id_familia == med_fam_id)
                    item_vat = Decimal("0.0000") if is_med else Decimal(str(vat_rate)).quantize(Decimal("0.0001"))
                    val_amount = (Decimal(str(affected)) * unit_cost).quantize(Decimal("0.0001"))
                    days_ago = random.randint(0, 30)
                    scan_ts = datetime.utcnow() - timedelta(days=days_ago, minutes=random.randint(1, 720))
                    obs = random.choice(shrinkage_reasons)

                    matching_stock = next((st for st in stocks if st.id_articulo == art.id_articulo), None)
                    wh_id = matching_stock.id_deposito if matching_stock else 1
                    br_id = matching_stock.id_sucursal if matching_stock else 1

                    audit_rec = AuditRecord(
                        tenant_id=1,
                        session_id=ws_id,
                        branch_id=br_id,
                        warehouse_id=wh_id,
                        article_code=art.id_articulo.strip(),
                        user_id=new_users[0].user_id if new_users else 1,
                        action_type="REMOVAL",
                        affected_amount=affected,
                        audit_quantity=max(0, (matching_stock.stock_real if matching_stock else 10) - affected),
                        applied_unit_cost=unit_cost,
                        applied_vat_rate=item_vat,
                        valorized_amount=val_amount,
                        scan_timestamp=scan_ts,
                        client_uuid=str(uuid.uuid4()),
                        observation=obs
                    )
                    analytics_audits.append(audit_rec)

            if goods_received_rate > 0 and len(work_sessions) > 0:
                ws_id = work_sessions[0].session_id
                gr_count = math.ceil(count * goods_received_rate)
                gr_articles = random.sample(articulos, min(gr_count, len(articulos)))
                goods_received_reasons = [
                    "Ingreso mercadería",
                    "Alta por remito",
                    "Recepción proveedor",
                    "Ajuste por sobrante",
                    "Ingreso por compra"
                ]
                goods_action_types = ["ADDITION", "Alta", "Ingreso"]
                for art in gr_articles:
                    affected = random.randint(5, 50)
                    unit_cost = art.pcio_com_siva or Decimal("100.00")
                    is_med = (art.id_familia == med_fam_id)
                    item_vat = Decimal("0.0000") if is_med else Decimal(str(vat_rate)).quantize(Decimal("0.0001"))
                    val_amount = (Decimal(str(affected)) * unit_cost).quantize(Decimal("0.0001"))
                    days_ago = random.randint(0, 30)
                    scan_ts = datetime.utcnow() - timedelta(days=days_ago, minutes=random.randint(1, 720))
                    obs = random.choice(goods_received_reasons)
                    act_type = random.choice(goods_action_types)

                    matching_stock = next((st for st in stocks if st.id_articulo == art.id_articulo), None)
                    wh_id = matching_stock.id_deposito if matching_stock else 1
                    br_id = matching_stock.id_sucursal if matching_stock else 1

                    audit_rec = AuditRecord(
                        tenant_id=1,
                        session_id=ws_id,
                        branch_id=br_id,
                        warehouse_id=wh_id,
                        article_code=art.id_articulo.strip(),
                        user_id=new_users[0].user_id if new_users else 1,
                        action_type=act_type,
                        affected_amount=affected,
                        audit_quantity=(matching_stock.stock_real if matching_stock else 10) + affected,
                        applied_unit_cost=unit_cost,
                        applied_vat_rate=item_vat,
                        valorized_amount=val_amount,
                        scan_timestamp=scan_ts,
                        client_uuid=str(uuid.uuid4()),
                        observation=obs
                    )
                    analytics_audits.append(audit_rec)

            if analytics_audits:
                s_analytics.raw_session.add_all(analytics_audits)
                await s_analytics.raw_session.flush()

            # 11. Seed DailyReports (db_analytics)
            daily_reports = []
            for t_obj in rec_tenants:
                for b_id in [1, 2]:
                    for days_ago in [1, 2, 3]:
                        rep_date = date.today() - timedelta(days=days_ago)
                        audited_skus = random.randint(max(10, len(articulos) // 4), max(11, len(articulos) // 2))
                        add_amt = random.randint(30, 200)
                        shrink_amt = random.randint(5, 40)
                        proc_units = add_amt + shrink_amt

                        add_val = (Decimal(str(random.randint(15000, 50000))) + Decimal(str(round(random.random(), 4)))).quantize(Decimal('0.0001'))
                        shrink_val = (Decimal(str(random.randint(1000, 8000))) + Decimal(str(round(random.random(), 4)))).quantize(Decimal('0.0001'))
                        net_variation = (add_val - shrink_val).quantize(Decimal('0.0001'))

                        daily_reports.append(DailyReport(
                            tenant_id=t_obj.tenant_id,
                            branch_id=b_id,
                            report_date=rep_date,
                            total_audit_articles=audited_skus,
                            total_processed_units=proc_units,
                            total_addition_amount=add_amt,
                            total_shrinkage_amount=shrink_amt,
                            total_addition_value=add_val,
                            total_shrinkage_value=shrink_val,
                            net_patrimonial_variation=net_variation
                        ))
            s_analytics.raw_session.add_all(daily_reports)

            # 12. Seed CriticalShrinkageAlerts (db_analytics)
            critical_alerts = []
            for lot in lotes:
                lot_venc_date = datetime.strptime(lot.vencimiento, "%Y-%m-%d").date()
                if lot_venc_date < date.today() + timedelta(days=30):
                    days_to_exp = (lot_venc_date - date.today()).days
                    risk = RiskLevel.RED if days_to_exp <= 0 else (RiskLevel.YELLOW if days_to_exp <= 30 else RiskLevel.GREEN)
                    art_ref = next((a for a in articulos if a.id_articulo == lot.id_articulo), articulos[0])
                    amt_at_risk = Decimal(str(lot.stock_real)) * Decimal(str(art_ref.pcio_com_siva))

                    critical_alerts.append(CriticalShrinkageAlert(
                        tenant_id=1,
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
            active_count = sum(1 for u in new_users if u.is_active)
            inactive_count = sum(1 for u in new_users if not u.is_active)
            print(f"   • Users (db_users): {len(new_users)} (Active: {active_count}, Inactive: {inactive_count})")
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
    parser.add_argument("--deposits", type=int, default=1, help="Number of virtual deposits.")
    parser.add_argument("--ghost-rate", type=float, default=0.10, help="Fraction of Ghost items.")
    parser.add_argument("--expired-rate", type=float, default=0.25, help="Fraction of expired lots.")
    parser.add_argument("--vat-rate", type=float, default=0.21, help="Default VAT rate for taxable items.")
    parser.add_argument("--shrinkage-rate", type=float, default=0.30, help="Fraction of articles with shrinkage audit records.")
    parser.add_argument("--goods-received-rate", type=float, default=0.15, help="Fraction of articles with goods received audit records.")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL override.")
    args = parser.parse_args()

    asyncio.run(run_seed(
        count=args.count,
        seed_val=args.seed,
        num_deposits=args.deposits,
        ghost_rate=args.ghost_rate,
        expired_rate=args.expired_rate,
        vat_rate=args.vat_rate,
        shrinkage_rate=args.shrinkage_rate,
        goods_received_rate=args.goods_received_rate,
        database_url=args.db_url
    ))
