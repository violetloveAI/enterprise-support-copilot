from services.mock_erp.app.database import seed_database

if __name__ == "__main__":
    path = seed_database(force=True)
    print(f"Seeded synthetic ERP database: {path}")
